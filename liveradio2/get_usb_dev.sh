sudo blkid -c /dev/null | awk 'BEGIN{FS=":"}/1/{if (($1!="/dev/mmcblk0p1") && ($1!="/dev/mmcblk0p2")) print $1}' > dev_usb.txt
