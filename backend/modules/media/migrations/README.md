# Migrations

MediaAsset stores only opaque private object keys and normalized photo metadata. Identity evidence is a separate storage bucket; it is never part of the public listing serializer. All uploaded images are awaiting review by default. Do not add public URLs, original filenames or national identification numbers to this table.
