#!/usr/bin/env python3
"""Patches lightpanda-io/zig-v8-fork so V8 can be built for aarch64-linux-android.

usage: patch_zig_v8.py <build.zig> [<build-tools/.gn>]

The upstream build only knows desktop Linux, macOS and iOS. For Android it needs gclient to fetch the
Android toolchain (target_os), gn to be told the target OS/CPU, and the gn dotfile to allow the one
expand_directory call the Android build makes.
"""
import sys

path = sys.argv[1]
s = open(path).read()

# 1) gn args: a separate branch for Android that returns before the Linux/clang-23 special case.
marker = "        switch (tag) {\n            .ios => {"
assert marker in s, "GnArgs switch not found"
android = (
    "        if (target.result.abi == .android) {\n"
    '            try args.appendSlice(gpa, "target_os=\\"android\\"\\n");\n'
    '            try args.appendSlice(gpa, "target_cpu=\\"arm64\\"\\n");\n'
    "            // Embed the snapshot in the library; there is no data directory next to an Android app binary.\n"
    '            try args.appendSlice(gpa, "v8_use_external_startup_data=false\\n");\n'
    '            try args.appendSlice(gpa, "treat_warnings_as_errors=false\\n");\n'
    '            try args.appendSlice(gpa, "clang_use_chrome_plugins=false\\n");\n'
    "            return gpa.dupe(u8, args.items);\n"
    "        }\n\n"
)
s = s.replace(marker, android + marker, 1)

# 2) .gclient: also fetch the Android dependencies (NDK, sysroot, build tools).
old = "        \\\\]\n        \\\\\n    , .{V8_VERSION});"
assert old in s, ".gclient template not found"
s = s.replace(old, '        \\\\]\n        \\\\target_os = ["android"]\n        \\\\\n    , .{V8_VERSION});', 1)

open(path, "w").write(s)
print("patched", path)

# 3) The dotfile zig-v8-fork stages for gn has no allowlists. Android's build reaches
#    //build/modules/BUILD.gn, which calls expand_directory; gn refuses that unless the dotfile
#    lists the caller. Chromium keeps the approved list in //build/dotfile_settings.gni.
if len(sys.argv) > 2:
    gn_path = sys.argv[2]
    g = open(gn_path).read()
    anchor = 'script_executable = "python3"\n'
    assert anchor in g, ".gn script_executable line not found"
    addition = (
        '\nimport("//build/dotfile_settings.gni")\n'
        "expand_directory_allowlist = build_dotfile_settings.expand_directory_allowlist\n"
    )
    g = g.replace(anchor, anchor + addition, 1)
    open(gn_path, "w").write(g)
    print("patched", gn_path)
