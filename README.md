# Lightpanda, natively on Android (experiment)

Goal: build [Lightpanda](https://github.com/lightpanda-io/browser) for Android's own C library, so an
app can run it without the glibc loader used by
[lightpanda-droid](https://github.com/cimon-bkr/lightpanda-droid).

Stages:

1. **V8 for Android** (`v8-android.yml`): builds Lightpanda's V8 wrapper (`libc_v8.a`) for
   aarch64-linux-android from source. This is the long one.
2. Cross-compile the Rust HTML parser for Android.
3. Build Lightpanda itself for aarch64-linux-android against the NDK and the archive from stage 1.
4. Package it in the app.

Status: stage 1 in progress.
