Dim Shell, Shortcut, Fso, Pathspec
Set Shell = CreateObject("WScript.Shell")
Set Fso = CreateObject("Scripting.FileSystemObject")
Pathspec = (Shell.SpecialFolders("Desktop") & "\Kalender.lnk")

If (Fso.FileExists(Pathspec)) Then
    Fso.DeleteFile(Pathspec)
End If

Set Shortcut = Shell.CreateShortcut(Shell.SpecialFolders("Desktop") & "\Kalender.lnk")
Shortcut.TargetPath = "C:\Python27\pythonw.exe"
Shortcut.WorkingDirectory = Fso.GetAbsolutePathName(".")
Shortcut.IconLocation = Fso.GetAbsolutePathName("kalender.ico")
Shortcut.Arguments = """" & Fso.GetAbsolutePathName("kalender.pyc") & """"
Shortcut.Save
