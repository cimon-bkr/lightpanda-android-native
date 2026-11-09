#!/usr/bin/env python3
"""Patches lightpanda-io/zig-v8-fork's build.zig so V8 can be built for aarch64-linux-android.

The upstream build only knows desktop Linux, macOS and iOS. For Android it needs gclient to fetch the
Android toolchain (target_os) and gn to be told the target OS/CPU. Everything else is unchanged.
"""
import sys

path = sys.argv[1]
s = open(path).read()

# 1) gn args: a separate branch for Android that returns before the Linux/clang-23 special case.
marker = "        switch (tag) {\n            .ios => {"
assert marker in s, "GnArgs switch not found"
android = '''        if (target.result.abi == .android) {
            try args.appendSlice(gpa, "target_os=\\"android\\"\\n");
            try args.appendSlice(gpa, "target_cpu=\\"arm64\\"\\n");
            // Embed the snapshot in the library; there is no data directory next to an Android app binary.
            try args.appendSlice(gpa, "v8_use_external_startup_data=false\\n");
            try args.appendSlice(gpa, "treat_warnings_as_errors=false\\n");
            try args.appendSlice(gpa, "clang_use_chrome_plugins=false\\n");
            return gpa.dupe(u8, args.items);
        }

'''
s = s.replace(marker, android + marker, 1)

# 2) .gclient: also fetch the Android dependencies (NDK, sysroot, build tools).
old = "        \\\\]\n        \\\\\n    , .{V8_VERSION});"
assert old in s, ".gclient template not found"
s = s.replace(old, "        \\\\]\n        \\\\target_os = [\"android\"]\n        \\\\\n    , .{V8_VERSION});", 1)

open(path, "w").write(s)
print("patched", path)
