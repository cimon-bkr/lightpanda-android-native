#!/usr/bin/env python3
"""Patches Lightpanda's build.zig for Android.

usage: patch_lightpanda.py <build.zig>

translate-c (the tool that turns C headers such as curl.h into Zig) looks up the C library's header
directories itself and ignores the --libc file, so for aarch64-linux-android it finds none. This
passes the NDK sysroot's headers to it explicitly, through a new -Dandroid_sysroot=<path> option.
"""
import sys

path = sys.argv[1]
s = open(path).read()

old = """fn translateC(b: *Build, mod: *Build.Module, header: Build.LazyPath) Translator {
    return .init(b.dependency("translate_c", .{}), .{
        .c_source_file = header,
        .target = mod.resolved_target.?,
        .optimize = mod.optimize.?,
        // Zig 0.16's built-in translate-c defaulted to this.
        .default_init = true,
    });
}
"""
assert old in s, "translateC helper not found (different Lightpanda version?)"

new = """var android_sysroot_loaded = false;
var android_sysroot: ?[]const u8 = null;

fn translateC(b: *Build, mod: *Build.Module, header: Build.LazyPath) Translator {
    const translator: Translator = .init(b.dependency("translate_c", .{}), .{
        .c_source_file = header,
        .target = mod.resolved_target.?,
        .optimize = mod.optimize.?,
        // Zig 0.16's built-in translate-c defaulted to this.
        .default_init = true,
    });
    // translate-c cannot find Android's headers by itself, so give them to it.
    if (mod.resolved_target.?.result.abi == .android) {
        if (!android_sysroot_loaded) {
            android_sysroot_loaded = true;
            android_sysroot = b.option([]const u8, "android_sysroot", "Path to the Android NDK sysroot");
        }
        if (android_sysroot) |sysroot| {
            translator.run.addArgs(&.{
                "-isystem", b.fmt("{s}/usr/include/aarch64-linux-android", .{sysroot}),
                "-isystem", b.fmt("{s}/usr/include", .{sysroot}),
                // Bionic's headers refuse an unversioned target and pull in fortify wrappers that
                // translate-c cannot parse.
                "-D__ANDROID_API__=29",
                "-D_FORTIFY_SOURCE=0",
            });
        }
    }
    return translator;
}
"""
s = s.replace(old, new, 1)
open(path, "w").write(s)
print("patched", path)
