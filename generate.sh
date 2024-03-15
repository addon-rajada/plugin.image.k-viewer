cd ..
zip -r -u -9 -T plugin.image.k-viewer.zip plugin.image.k-viewer/ \
-x "plugin.image.k-viewer/.git/*" \
-x "plugin.image.k-viewer/resources/lib/check/*" \
-x "plugin.image.k-viewer/*/__pycache__/*"
