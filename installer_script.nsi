!ifndef PRODUCT_VERSION
  !define PRODUCT_VERSION "0.0.0"
!endif

!define PRODUCT_NAME "LANCryptor"
!define PRODUCT_PUBLISHER "Your Company or Name"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"

OutFile "release\LANCryptor-setup-${PRODUCT_VERSION}.exe"
InstallDir "$PROGRAMFILES\LANCryptor"

Page directory
Page instfiles
UninstPage uninstConfirm
UninstPage instfiles

Section "Install"
  SetOutPath "$INSTDIR"

  File "dist\LANCryptor.exe"
  File "README.md"
  File "LICENSE"

  CreateShortcut "$DESKTOP\LANCryptor.lnk" "$INSTDIR\LANCryptor.exe"

  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayName" "${PRODUCT_NAME}"
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\uninstall.exe"
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"

  WriteUninstaller "$INSTDIR\uninstall.exe"
SectionEnd

Section "Uninstall"
  Delete "$INSTDIR\LANCryptor.exe"
  Delete "$INSTDIR\README.md"
  Delete "$INSTDIR\LICENSE"
  Delete "$INSTDIR\uninstall.exe"
  Delete "$DESKTOP\LANCryptor.lnk"
  RMDir "$INSTDIR"
  DeleteRegKey HKLM "${PRODUCT_UNINST_KEY}"
SectionEnd
