# FlashForge Integration Migration Guide

## Version 0.3.0 - Major Update

This version migrates from the legacy `ffpp` library to the modern `flashforge-python-api` library, bringing significant improvements and new features.

## 🎉 New Features

### 1. **Time Remaining Sensor**
- New sensor: `sensor.flashforge_print_time_remaining` (in seconds)
- New sensor: `sensor.flashforge_print_eta` (formatted time)
- New sensor: `sensor.flashforge_print_duration` (elapsed time)

### 2. **Print Thumbnails**
- New image entity: `image.flashforge_print_thumbnail`
- Automatically fetches and displays thumbnail for the current print job
- Shows as a standard Home Assistant image entity

### 3. **Fan/Air Control**
- **Cooling Fan**: `fan.flashforge_cooling_fan` with speed control (0-100%)
- **Chamber Fan**: `fan.flashforge_chamber_fan` with speed control (0-100%)
- **External Filtration**: `fan.flashforge_external_filtration` (on/off for 5M Pro)
- **Internal Filtration**: `fan.flashforge_internal_filtration` (on/off for 5M Pro)

### 4. **Door Sensor**
- New binary sensor: `binary_sensor.flashforge_door`
- Shows open/closed state of printer enclosure door

### 5. **File Upload Service**
- New service: `flashforge.upload_file`
- Parameters:
  - `file_path`: Path to local G-code file
  - `start_print`: Whether to start printing after upload (default: false)
  - `level_before_print`: Whether to level bed before print (default: false)

## 📦 Breaking Changes

### Configuration Changes
The integration now requires two additional optional parameters:
- `serial_number`: Printer serial number (can be auto-detected)
- `check_code`: Authentication code (can be empty for local networks)

### API Migration
- Replaced `ffpp==0.0.15` with `flashforge-python-api==1.0.0`
- All internal API calls updated to use the new library
- Improved error handling and connection stability

### Sensor Changes
- Temperature sensors now use the standard Home Assistant temperature device class
- All sensors have improved metadata and device classes
- Sensor names may have changed slightly (check entity IDs)

## 🔧 Installation Instructions

### Manual Installation
1. **Update dependencies**:
   ```bash
   pip install flashforge-python-api==1.0.0
   ```

2. **Update integration files**:
   - Replace all files in `custom_components/flashforge/` with the new versions
   - Key files updated:
     - `__init__.py` - Core integration logic
     - `manifest.json` - Version and dependencies
     - `sensor.py` - All sensors including new time sensors
     - `fan.py` - NEW: Fan control platform
     - `binary_sensor.py` - NEW: Door sensor
     - `image.py` - NEW: Thumbnail display
     - `config_flow.py` - Updated discovery and setup
     - `data_update_coordinator.py` - Updated API calls

3. **Restart Home Assistant**

### HACS Installation
1. Wait for the update to be available in HACS
2. Update through HACS interface
3. Restart Home Assistant

## 🔄 Migration Steps

### For Existing Users

1. **Backup your configuration**
   - Note your current sensor entity IDs
   - Export any automations using FlashForge entities

2. **Update the integration**
   - Follow installation instructions above

3. **Reconfigure if needed**
   - The integration should automatically migrate
   - If prompted, re-add the printer through the UI
   - Discovery should work automatically

4. **Update automations**
   - Check sensor entity IDs (they should remain the same)
   - Add new entities to automations as desired

## 📊 New Entity Overview

### Sensors (16 total)
- `sensor.flashforge_status` - Printer status
- `sensor.flashforge_job_percentage` - Print progress (%)
- `sensor.flashforge_file` - Current file name
- `sensor.flashforge_current_layer` - Current layer number
- `sensor.flashforge_total_layers` - Total layers
- `sensor.flashforge_print_time_remaining` - **NEW** Time left (seconds)
- `sensor.flashforge_print_eta` - **NEW** Estimated completion time
- `sensor.flashforge_print_duration` - **NEW** Elapsed time (seconds)
- `sensor.flashforge_bed_temp` - Bed temperature
- `sensor.flashforge_bed_target_temp` - Bed target temperature
- `sensor.flashforge_extruder_temp` - Extruder temperature
- `sensor.flashforge_extruder_target_temp` - Extruder target temperature

### Binary Sensors (1 total)
- `binary_sensor.flashforge_door` - **NEW** Door open/closed

### Fans (4 total)
- `fan.flashforge_cooling_fan` - **NEW** Cooling fan control
- `fan.flashforge_chamber_fan` - **NEW** Chamber fan control
- `fan.flashforge_external_filtration` - **NEW** External filter (5M Pro)
- `fan.flashforge_internal_filtration` - **NEW** Internal filter (5M Pro)

### Images (1 total)
- `image.flashforge_print_thumbnail` - **NEW** Current print thumbnail

### Lights (1 total)
- `light.flashforge_light` - LED control (unchanged)

### Buttons (4 total)
- `button.flashforge_abort` - Abort print (unchanged)
- `button.flashforge_continue` - Resume print (unchanged)
- `button.flashforge_pause` - Pause print (unchanged)
- `button.flashforge_print_file` - Start print (unchanged)

### Select (1 total)
- `select.flashforge_file_list` - File selection (unchanged)

## 🎯 Example Automations

### Send Notification When Print Complete
```yaml
automation:
  - alias: "Print Complete Notification"
    trigger:
      - platform: state
        entity_id: sensor.flashforge_status
        to: "completed"
    action:
      - service: notify.mobile_app
        data:
          title: "Print Complete!"
          message: "Your 3D print has finished"
          data:
            image: /api/image_proxy/image.flashforge_print_thumbnail
```

### Alert When Door Opens During Print
```yaml
automation:
  - alias: "Door Opened During Print"
    trigger:
      - platform: state
        entity_id: binary_sensor.flashforge_door
        to: "on"
    condition:
      - condition: state
        entity_id: sensor.flashforge_status
        state: "printing"
    action:
      - service: notify.mobile_app
        data:
          title: "Warning!"
          message: "Printer door opened during print"
```

### Auto-Enable Filtration When Printing
```yaml
automation:
  - alias: "Enable Filtration During Print"
    trigger:
      - platform: state
        entity_id: sensor.flashforge_status
        to: "printing"
    action:
      - service: fan.turn_on
        target:
          entity_id: fan.flashforge_external_filtration
  
  - alias: "Disable Filtration After Print"
    trigger:
      - platform: state
        entity_id: sensor.flashforge_status
        to: "completed"
    action:
      - service: fan.turn_off
        target:
          entity_id: fan.flashforge_external_filtration
```

### Upload and Start Print Service Call
```yaml
action:
  - service: flashforge.upload_file
    data:
      file_path: "/config/gcode/test_print.gcode"
      start_print: true
      level_before_print: true
```

## 🐛 Troubleshooting

### Integration Won't Load
1. Check Home Assistant logs for errors
2. Verify `flashforge-python-api` is installed: `pip list | grep flashforge`
3. Try removing and re-adding the integration

### Printer Not Discovered
1. Ensure printer is on and connected to network
2. Check that Home Assistant and printer are on same network/VLAN
3. Try manual configuration with IP address

### Some Entities Missing
- **Fan entities**: Only appear if printer supports them (5M Pro for filtration)
- **Thumbnail**: Only appears when actively printing
- **Door sensor**: Only if printer has door sensor hardware

### Connection Issues
- Verify IP address hasn't changed (use DHCP reservation)
- Check firewall rules (ports 8898, 8899)
- Ensure no other software is connecting to printer

## 📝 Notes

- **5M Pro Features**: External/internal filtration fans only available on 5M Pro models
- **Thumbnail Support**: Thumbnails embedded in G-code by slicers like OrcaSlicer
- **Performance**: Polling interval is 30 seconds (configurable in const.py)
- **Backward Compatibility**: Existing entity IDs should remain unchanged

## 🆘 Support

- **Issues**: https://github.com/joseffallman/hass_flashforge/issues
- **Documentation**: https://github.com/joseffallman/hass_flashforge
- **API Library**: https://github.com/GhostTypes/ff-5mp-api-py

## 📜 Changelog

### Version 0.3.0 (Current)
- ✨ Added time remaining sensors (time_remaining, eta, duration)
- ✨ Added print thumbnail image entity
- ✨ Added fan control platform (cooling, chamber, filtration)
- ✨ Added door sensor binary sensor
- ✨ Added file upload service
- 🔄 Migrated from ffpp to flashforge-python-api
- 🐛 Improved error handling and connection stability
- 📚 Updated dependencies to latest versions

### Version 0.2.1 (Previous)
- Used ffpp library
- Basic sensor and camera support
