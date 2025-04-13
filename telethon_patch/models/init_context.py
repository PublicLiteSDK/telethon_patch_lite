import enum

from telethon_patch.models.json_context import JsonContent


class InitContext:
    app_id: int = None
    app_hash: str = None
    device_model: str = None
    system_version: str = None
    app_version: str = None
    lang_code: str = None
    system_lang_code: str = None

    @staticmethod
    def load_from_json_context(json_content: JsonContent):
        init_context = InitContext()
        init_context.app_id = json_content.app_id
        init_context.app_hash = json_content.app_hash
        init_context.device_model = json_content.device
        init_context.system_version = json_content.sdk
        init_context.app_version = json_content.app_version
        init_context.lang_code = json_content.lang_pack
        init_context.system_lang_code = json_content.system_lang_pack

        return init_context

    def __dict__(self):
        return dict(
            app_id=self.app_id,
            app_hash=self.app_hash,
            device_model=self.device_model,
            system_version=self.system_version,
            app_version=self.app_version,
            lang_code=self.lang_code,
            system_lang_code=self.system_lang_code
        )
