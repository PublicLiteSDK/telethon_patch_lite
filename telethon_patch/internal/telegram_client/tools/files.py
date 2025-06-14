import enum
import os
import shutil
import typing

from telethon.sessions import SQLiteSession

if typing.TYPE_CHECKING:
    from telethon_patch import TelegramClient


class FilesError(Exception):
    pass


class FileHandlerTypes(enum.Enum):
    GET = enum.auto()
    REMOVE = enum.auto()
    MOVE = enum.auto()
    COPY = enum.auto()
    RENAME = enum.auto()


class FilesMethods:
    @staticmethod
    def _validate_dir(dir_path: str):
        if not os.path.realpath(dir_path):
            raise FilesError('Provided directory path is invalid')

    @staticmethod
    def _ensure_dir(path: str):
        # print([path])

        # dir_name = os.path.dirname(path)
        # print([path, dir_name])

        if not os.path.exists(path):
            # print([path])
            os.makedirs(path, exist_ok=True)

    def _get_path(self: "TelegramClient", index: int) -> typing.Optional[str]:
        return {
            0: self.session_context.filename,
            1: self.json_context.filename
        }.get(index, None)

    def _set_path(self: "TelegramClient", index: int, path: str):
        match index:
            case 0:
                self.session_context.filename = path
            case 1:
                self.json_context.filename = path

    def _file_handler(
            self: "TelegramClient",
            file_indexes: list[bool],
            method: FileHandlerTypes = None,
            new_dir: str = None,
            rename_value: str = None
    ) -> str:
        # print([new_dir])

        if method in {FileHandlerTypes.MOVE, FileHandlerTypes.COPY}:
            if new_dir is None:
                return False

            self._ensure_dir(new_dir)

        for index, use in enumerate(file_indexes):
            if use is False:
                continue

            path = self._get_path(index)
            if path is None or not os.path.isfile(path):
                continue

            match method:
                case FileHandlerTypes.REMOVE:
                    os.remove(path)
                    self._set_path(index, None)

                case FileHandlerTypes.MOVE:
                    new_path = os.path.join(new_dir, os.path.basename(path))
                    if os.path.exists(new_path):
                        os.remove(new_path)
                    # print([index, path, new_path])
                    os.rename(path, new_path)
                    self._set_path(index, new_path)

                case FileHandlerTypes.RENAME:
                    new_path = os.path.join(
                        os.path.dirname(path),
                        "{}.{}".format(rename_value, path.split('.')[-1])
                    )
                    if os.path.exists(new_path):
                        os.remove(new_path)
                    os.rename(path, new_path)
                    self._set_path(index, new_path)

                case FileHandlerTypes.COPY:
                    new_path = os.path.join(new_dir, os.path.basename(path))
                    if os.path.exists(new_path):
                        os.remove(new_path)

                    shutil.copyfile(path, new_path)

        return True

    async def move(self: "TelegramClient", new_dir: str, move_session: bool = True, move_json: bool = True) -> bool:
        self._validate_dir(new_dir)
        return self._file_handler([move_session, move_json], FileHandlerTypes.MOVE, new_dir)

    async def copy(self: "TelegramClient", new_dir: str, copy_session: bool = True, copy_json: bool = True) -> bool:
        self._validate_dir(new_dir)
        return self._file_handler([copy_session, copy_json], FileHandlerTypes.COPY, new_dir)

    async def remove(self: "TelegramClient", del_session: bool = True, del_json: bool = True) -> bool:
        return self._file_handler([del_session, del_json], FileHandlerTypes.REMOVE)

    async def rename(self: "TelegramClient", new_file_name: str) -> bool:
        return self._file_handler([True, True], FileHandlerTypes.RENAME, rename_value=new_file_name)
