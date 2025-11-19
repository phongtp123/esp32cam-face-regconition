# Distributed under the OSI-approved BSD 3-Clause License.  See accompanying
# file Copyright.txt or https://cmake.org/licensing for details.

cmake_minimum_required(VERSION 3.5)

file(MAKE_DIRECTORY
  "/home/r_and_tung/esp/esp-idf/components/bootloader/subproject"
  "/home/r_and_tung/esp32cam-face-regconition/build/bootloader"
  "/home/r_and_tung/esp32cam-face-regconition/build/bootloader-prefix"
  "/home/r_and_tung/esp32cam-face-regconition/build/bootloader-prefix/tmp"
  "/home/r_and_tung/esp32cam-face-regconition/build/bootloader-prefix/src/bootloader-stamp"
  "/home/r_and_tung/esp32cam-face-regconition/build/bootloader-prefix/src"
  "/home/r_and_tung/esp32cam-face-regconition/build/bootloader-prefix/src/bootloader-stamp"
)

set(configSubDirs )
foreach(subDir IN LISTS configSubDirs)
    file(MAKE_DIRECTORY "/home/r_and_tung/esp32cam-face-regconition/build/bootloader-prefix/src/bootloader-stamp/${subDir}")
endforeach()
if(cfgdir)
  file(MAKE_DIRECTORY "/home/r_and_tung/esp32cam-face-regconition/build/bootloader-prefix/src/bootloader-stamp${cfgdir}") # cfgdir has leading slash
endif()
