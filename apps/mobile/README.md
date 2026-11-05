# Anima Flutter mobile app (Android + iOS)

The mobile source is real Flutter code, but native runner directories are **not** committed yet. Generate the standard Android and iOS shells with the official Flutter CLI in this folder. Do NOT use a generic WebView wrapper.

## Install
- Flutter stable: https://docs.flutter.dev/get-started/install
- Android Studio + Android SDK; run `flutter doctor -v`.
- iOS requires macOS and Xcode for signing/simulator/archiving, plus Apple Developer membership for external distribution.

## Bootstrap standard Android/iOS runners
```sh
cd apps/mobile
flutter create --platforms=android,ios --project-name anima_app --org com.anima .
flutter pub get
flutter analyze
flutter test
```

`flutter create` preserves existing source files by default. Commit generated native runners on a reviewed follow-up PR after actual app identifier, organization/domain and signing ownership are agreed. The current `com.anima` identifier is **temporary**, not production-registered.

## Connect to development API
Start root `docker compose --profile app up --build -d`. The API is available at http://127.0.0.1:8000. On a USB-connected Android phone:
```sh
adb reverse tcp:8000 tcp:8000
flutter run --dart-define=API_BASE_URL=http://127.0.0.1:8000
```
For Android emulator use `http://10.0.2.2:8000` as the API_BASE_URL. On iOS simulator use `http://127.0.0.1:8000`. On a physical iPhone use an explicitly authorized LAN IP or staging HTTPS origin; configure debug-only transport exceptions if HTTP is used locally. **Never ship a production build that permits unrestricted cleartext traffic.** Android's generated runner may require debug-only cleartext permission for local HTTP; prefer HTTPS staging if unavailable.

## Implemented mobile functionality
Five-tab shell, light/dark styling, real API market list with loading/error/empty/retry states, email registration, sign-in, token-based email verification, session persistence via platform secure storage, seller application pending manual staff review. Tab screens for video creation and chat truthfully state that those features are not implemented. No live payment or animal trade promise.

## Security
Do not embed secret API tokens, user passwords or payment keys in Dart defines or source. All money and listing permissions are enforced on backend. Dart --dart-define is build-time configuration, not secret storage. Store refresh/access tokens in Flutter Secure Storage; production network must use HTTPS.

## Test APK from CI
After the Android build job passes, open the successful **Flutter quality** GitHub Actions run and download the `anima-m0-debug-apk` artifact. It is an unsigned-for-distribution debug build for development devices only. Use `adb reverse tcp:8000 tcp:8000` on a USB-connected Android phone if the app should reach the local API. Do not publish the debug APK to Play Store. Its application ID is temporary.

## Known limitations
- Backend does not serve real media, feed, live chat, seller listing creation UI or checkout yet.
- Default list is empty until admins approve sellers and permitted species then manually approve submitted listings.
- Error reporting and design system will be enhanced after M0.
- Store assets, final app ID, launcher icons and signing are pending brand/client approval.
