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

After email verification and submission of a pending or approved seller application, use **Create → Create listing** (or **Profile → Manage animal listings**) to save an individual-animal draft. Then choose **Manage photos** on that draft. For private seller documents, visit **Profile → Upload animal photos or verification**.

The upload screen allows:
- Choosing JPEG/PNG photos from the Android/iOS gallery.
- Attaching up to eight photos to a seller-owned **draft** animal listing created directly in the app.
- Choosing a seller-verification evidence category, checking consent and uploading private document photographs.
- Viewing photo gallery previews and review states, removing draft photos with an audit trail, and refreshing the list.
- Saving private verification files without exposing cloud object keys to the app.

The photo reviewer must approve listing photos before they can become public on an approved active listing. Seller evidence remains private even after seller review. HEIC, animated GIF, PDFs and videos are unsupported. The app can now create and edit individual-animal drafts, with species-category guidance and integer-precise NGN pricing. Seller submission requires an approved seller, permitted species and at least one uploaded photo; staff publication requires an approved photo. Litter/lot inventory and species-specific medical/health record modules remain unbuilt. Production real-device iOS testing, cloud R2 setup and final privacy/retention agreements are still required.

The `image_picker` plugin requires an iOS photo-library purpose string. The generator helper above adds it to the temporary native runner. The final, client-owned Xcode project must retain this entry and be reviewed in a macOS/iOS build; an Android CI build does not prove iOS release readiness.

## Account recovery (M1 partial)

From the signed-out **Profile** screen, tap **Forgot password?**. Enter your registered email and request a 20-minute recovery code; unknown addresses receive the same generic response. Enter the code and a new valid password to change the account password and invalidate older devices' JWT sessions. Unverified users can also **Resend verification code** with an account cooldown. The mobile screen and backend are covered by automated tests; real SMTP and real Android/iOS end-to-end tests remain outstanding. See [the security runbook](../../docs/26-account-recovery.md).

## Session security: sign out everywhere (CI-tested)

The signed-in Profile screen now includes **Sign out on all devices**. A person enters their existing password and confirms the action. After server authorization and a successful all-device revocation, this phone clears its secure JWT tokens and returns to sign-in. If the password is wrong or the server cannot confirm, the app displays an error and does not claim other sessions were revoked. See [the account-security runbook](../../docs/26-account-recovery.md). The feature has passing backend/Flutter/Android CI, but has **not** been accepted on physical Android/iOS devices or a production account. A device-management list and staff MFA are still unavailable.

## Creator video upload (under development; disabled without Stream)

The Create tab now offers **Post an animal video** and the existing **List or manage an animal** workflow. The video screen checks the server capability flag before exposing video selection, accepts MP4/MOV under 200 MB, requires a caption and footage-rights/animal-topic attestation, requests a private upload ticket, transfers directly to trusted Stream storage, and displays private processing/moderation status. No approved public publication flow or live Cloudflare integration is claimed. See [creator-video guide](../../docs/30-creator-video-ux.md).

## Video-first Home (PR #29 merged; real-device validation pending)

The owner specified a short-form video feed as the first screen. The Home tab now targets a full-height, vertically swipable HLS player (Flutter `video_player`), an animal creator/caption overlay, visible-clip-only playback, play/pause and mute controls, next-page loading and eligible linked-listing details.

The server only exposes fully processed, moderator-approved videos. No creator upload/webhook/automated media processing or commercial video inventory is active. Until Cloudflare Stream and human moderation are configured, visitors see a **truthful empty feed** and a shortcut to the marketplace. No fake videos or simulated engagement. Backend and Flutter CI passed (78 backend tests and 4 subtests, 19 Flutter tests, static analysis), and Android debug APK compiled. Actual Android/iOS video-playback and low-bandwidth acceptance remain untested. [Read the video-first decision](../../docs/28-video-first-product-decision.md).

## Implemented mobile functionality
Five-tab shell with video-first Home (development PR pending), light/dark styling, real API market list with loading/error/empty/retry states, email registration, sign-in, token-based email verification, session persistence via platform secure storage, seller application pending manual staff review, and the animal draft create/edit workspace, private image picker/gallery and seller evidence upload. The Create tab supports individual-animal listings; social video creation and chat truthfully state those features are not implemented. No live payment or animal trade promise.

## Security
Do not embed secret API tokens, user passwords or payment keys in Dart defines or source. All money and listing permissions are enforced on backend. Dart --dart-define is build-time configuration, not secret storage. Store refresh/access tokens in Flutter Secure Storage; production network must use HTTPS.

## Test APK from CI
After the Android build job passes, open the successful **Flutter quality** GitHub Actions run and download the `anima-m0-debug-apk` artifact. It is an unsigned-for-distribution debug build for development devices only. Use `adb reverse tcp:8000 tcp:8000` on a USB-connected Android phone if the app should reach the local API. Do not publish the debug APK to Play Store. Its application ID is temporary.

## Known limitations
- Backend serves approved animal images and private evidence through authorized API routes; mobile creation/editing of private individual-animal drafts and gallery upload/removal are implemented. Video-first player/read API are under review; video upload and live media processing, chat, health documents, group/litter inventory, real payment checkout and production deployment are not implemented.
- Default list is empty until admins approve sellers and permitted species then manually approve submitted listings.
- Error reporting and design system will be enhanced after M0.
- Store assets, final app ID, launcher icons and signing are pending brand/client approval.

See [seller listing workflow](../../docs/25-seller-listing-workflow.md) for exact API permissions, moderation states, partial M1 acceptance and remaining staging/device gates.
