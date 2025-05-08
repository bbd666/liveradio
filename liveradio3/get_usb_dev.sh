sudo blkid -c /dev/null | awk 'BEGIN{FS=":"}/1/{if (NR<2) print $1}' > dev_usb.txt
