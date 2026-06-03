# Compila firmware/firmware.ino para wokwi/build/ (caminho lido pelo wokwi.toml).
# Uso (de qualquer pasta):  pwsh iot-esp32/wokwi/build.ps1
# Requer arduino-cli no PATH + core esp32 e libs instalados (ver wokwi.toml).
$ErrorActionPreference = 'Stop'
$here   = Split-Path -Parent $MyInvocation.MyCommand.Path
$sketch = Join-Path $here '..\firmware\firmware.ino'
$out    = Join-Path $here 'build'

arduino-cli compile --fqbn esp32:esp32:esp32doit-devkit-v1 --output-dir $out $sketch
Write-Host "OK -> $out (firmware.ino.merged.bin + firmware.ino.elf)"
