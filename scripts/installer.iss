; =====================================================================
;  Inno Setup: Deadlock Mod Manager -> Setup_DLMM.exe
;
;  Сборка установщика:  iscc scripts\installer.iss
;  (перед этим выполнить scripts\build_exe.bat — нужен dist\DeadlockModManager)
;
;  Установщик (per-user, без прав администратора):
;    * ярлыки: меню «Пуск» + рабочий стол (по выбору)
;    * запись в «Установка и удаление программ»
;    * опционально: ассоциация ссылок deadlock-mod-manager://
;    * иконка приложения — assets\icon.ico
; =====================================================================

#define AppName "Deadlock Mod Manager"
#define AppExe "DeadlockModManager.exe"
#define AppVersion "1.0.0"
#define AppPublisher "Deadlock Mod Manager Contributors"
#define AppId "{{8C1A5E5F-7E28-4B77-9D9B-2F6C0A11D3AA}"

[Setup]
AppId={#AppId}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={localappdata}\Programs\{#AppName}
DefaultGroupName={#AppName}
UninstallDisplayIcon={app}\{#AppExe}
SetupIconFile=..\assets\icon.ico
OutputDir=..\dist\installer
OutputBaseFilename=Setup_DLMM
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "Создать ярлык на рабочем столе"; \
    GroupDescription: "Дополнительно:"
Name: "gbprotocol"; Description: "Открывать ссылки GameBanana (deadlock-mod-manager://) в приложении — установка модов в 1 клик"; \
    GroupDescription: "Дополнительно:"

[Files]
Source: "..\dist\DeadlockModManager\*"; DestDir: "{app}"; \
    Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{group}\Удалить {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Registry]
; URL-протокол для кнопки «Mod installer» на GameBanana
Root: HKCU; Subkey: "Software\Classes\deadlock-mod-manager"; \
    ValueType: string; ValueData: "URL:Deadlock Mod Manager"; \
    Flags: uninsdeletekey; Tasks: gbprotocol
Root: HKCU; Subkey: "Software\Classes\deadlock-mod-manager"; \
    ValueType: string; ValueName: "URL Protocol"; ValueData: ""; \
    Tasks: gbprotocol
Root: HKCU; Subkey: "Software\Classes\deadlock-mod-manager\DefaultIcon"; \
    ValueType: string; ValueData: "{app}\{#AppExe},0"; Tasks: gbprotocol
Root: HKCU; Subkey: "Software\Classes\deadlock-mod-manager\shell\open\command"; \
    ValueType: string; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: gbprotocol

[Run]
Filename: "{app}\{#AppExe}"; Description: "Запустить {#AppName}"; \
    Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Пользовательские данные (config.json, installed.json, скачанные моды)
; остаются в %APPDATA%\DeadlockModManager — удалять их за пользователя нельзя.
