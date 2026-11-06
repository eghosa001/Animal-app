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
python3 ../../scripts/configure_ios_photo_permissions.py ios/Runner/Info.plist
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

## Seller image uploads (M1 partial, staging UI)

After email verification and submission of a pending or approved seller application, visit **Profile → Upload animal photos or verification**.

The upload screen allows:
- Choosing JPEG/PNG photos from the Android/iOS gallery.
- Attaching up to eight photos to a seller-owned **draft** animal listing (a draft must already exist in the backend).
- Choosing a seller-verification evidence category, checking consent and uploading private document photographs.
- Viewing upload review states and refreshing the list.
- Saving private verification files without exposing cloud object keys to the app.

The photo reviewer must approve listing photos before they can become public on an approved active listing. Seller evidence remains private even after seller review. HEIC, animated GIF, PDFs and videos are unsupported. The app cannot yet create an animal listing from its own screen; that is a distinct verified M1 feature. Production real-device iOS testing, cloud R2 setup and final privacy/retention agreements are still required.

The `image_picker` plugin requires an iOS photo-library purpose string. The generator helper above adds it to the temporary native runner. The final, client-owned Xcode project must retain this entry and be reviewed in a macOS/iOS build; an Android CI build does not prove iOS release readiness.

## Implemented mobile functionality
Five-tab shell, light/dark styling, real API market list with loading/error/empty/retry states, email registration, sign-in, token-based email verification, session persistence via platform secure storage, seller application pending manual staff review, and private image picker/upload UI for existing draft listings and seller evidence. Tab screens for video creation and chat truthfully state that those features are not implemented. No live payment or animal trade promise.

## Security
Do not embed secret API tokens, user passwords or payment keys in Dart defines or source. All money and listing permissions are enforced on backend. Dart --dart-define is build-time configuration, not secret storage. Store refresh/access tokens in Flutter Secure Storage; production network must use HTTPS.

## Test APK from CI
After the Android build job passes, open the successful **Flutter quality** GitHub Actions run and download the `anima-m0-debug-apk` artifact. It is an unsigned-for-distribution debug build for development devices only. Use `adb reverse tcp:8000 tcp:8000` on a USB-connected Android phone if the app should reach the local API. Do not publish the debug APK to Play Store. Its application ID is temporary.

## Known limitations
- Backend serves approved animal images and private evidence through authorized API routes; mobile media upload now exists for existing drafts. Feed videos, live chat, new draft creation UI and checkout are still not implemented.
- Default list is empty until admins approve sellers and permitted species then manually approve submitted listings.
- Error reporting and design system will be enhanced after M0.
- Store assets, final app ID, launcher icons and signing are pending brand/client approval.
