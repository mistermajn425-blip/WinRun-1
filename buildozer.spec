[app]
title = WinRun
package.name = winrun
package.domain = org.winrun
source.dir = .
source.include_exts = py,png,json
source.exclude_dirs = tools,.github,bin,.buildozer,__pycache__
version = 1.0.0
requirements = python3,kivy
orientation = portrait
fullscreen = 1
icon.filename = %(source.dir)s/assets/icon.png
presplash.filename = %(source.dir)s/assets/art.png
presplash.color = #0e1424
android.minapi = 24
android.archs = arm64-v8a
android.accept_sdk_license = True
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
