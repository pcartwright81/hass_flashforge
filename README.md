# FlashForge 3D Printer

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![hacs][hacsbadge]][hacs]

_Integration to integrate with [FlashForge 3D printers][flashforge]._

**This integration will set up the following platforms.**

Platform | Description
-- | --
`sensor` | Show info from your 3D printer. <ul><li>Temperature sensors (bed and extruder)</li><li>Print progress and time remaining</li><li>Printer status</li><li>Current layer and total layers</li></ul>
`binary_sensor` | Door sensor showing open/closed state.
`fan` | Fan control for cooling, chamber, and air filtration (5M Pro models).
`image` | Print thumbnail display for current job.
`light` | LED control for printer lighting.
`button` | Control buttons for print operations (pause, resume, abort, start).
`select` | File selection dropdown for available print files.
`camera` | Printer camera if available.

## Features

### 🎯 Core Features
- **Real-time Monitoring**: Track print progress, temperatures, and status
- **Print Control**: Pause, resume, abort, and start prints from Home Assistant
- **File Management**: Upload files and select from printer's file list
- **Camera Integration**: View live camera feed if printer has camera
- **LED Control**: Toggle printer LED lighting

### 🆕 Advanced Features (v0.3.0+)
- **Time Tracking**: Print time remaining, ETA, and elapsed duration
- **Print Thumbnails**: View thumbnail of current print job
- **Fan Control**: 
  - Cooling fan with speed control (0-100%)
  - Chamber fan with speed control (0-100%)
  - External filtration (5M Pro)
  - Internal filtration (5M Pro)
- **Door Monitoring**: Binary sensor for enclosure door state
- **File Upload Service**: Upload and optionally start prints via service call

# Installation

## HACS Installation (Recommended)
1. Open HACS in Home Assistant
1. Click on the three dots in the top right corner
1. Select "Custom repositories"
1. Add `https://github.com/joseffallman/hass_flashforge` as an Integration
1. Click "Install"
1. Restart Home Assistant

## Manual Installation
1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`)
1. If you do not have a `custom_components` directory (folder) there, you need to create it
1. In the `custom_components` directory (folder) create a new folder called `flashforge`
1. Download _all_ the files from the `custom_components/flashforge/` directory (folder) in this repository
1. Place the files you downloaded in the new directory (folder) you created
1. Restart Home Assistant

## Configuration

Configuration is done through the Home Assistant UI:

1. In the HA UI go to "Configuration" → "Integrations" click "+" and search for "FlashForge"
1. Enter your printer's IP address
1. Optionally provide serial number and check code (can be auto-detected for local networks)
1. The integration will discover your printer and create all available entities

## Entities

### Sensors (12+)
- `sensor.flashforge_status` - Current printer status (see [Status Values](#status-values))
- `sensor.flashforge_job_percentage` - Print progress percentage
- `sensor.flashforge_file` - Current file name
- `sensor.flashforge_current_layer` - Current layer number
- `sensor.flashforge_total_layers` - Total layers in print
- `sensor.flashforge_print_time_remaining` - Time remaining (seconds)
- `sensor.flashforge_print_eta` - Estimated completion time
- `sensor.flashforge_print_duration` - Elapsed print time (seconds)
- `sensor.flashforge_bed_temp` - Bed temperature (°C)
- `sensor.flashforge_bed_target_temp` - Bed target temperature (°C)
- `sensor.flashforge_extruder_temp` - Extruder temperature (°C)
- `sensor.flashforge_extruder_target_temp` - Extruder target temperature (°C)

### Binary Sensors
- `binary_sensor.flashforge_door` - Door open/closed state

### Fans
- `fan.flashforge_cooling_fan` - Cooling fan with speed control
- `fan.flashforge_chamber_fan` - Chamber fan with speed control
- `fan.flashforge_external_filtration` - External air filter (5M Pro only)
- `fan.flashforge_internal_filtration` - Internal air filter (5M Pro only)

### Images
- `image.flashforge_print_thumbnail` - Current print thumbnail

### Lights
- `light.flashforge_light` - LED control

### Buttons
- `button.flashforge_pause` - Pause current print
- `button.flashforge_continue` - Resume paused print
- `button.flashforge_abort` - Cancel current print
- `button.flashforge_print_file` - Start selected print

### Select
- `select.flashforge_file_list` - Select file from printer storage

### Camera
- `camera.flashforge` - Live camera feed (if available)

## Services

### flashforge.upload_file
Upload a G-code file to the printer and optionally start printing.

**Parameters:**
- `file_path` (required): Path to local G-code file
- `start_print` (optional, default: false): Start printing after upload
- `level_before_print` (optional, default: false): Level bed before printing

**Example:**
```yaml
service: flashforge.upload_file
data:
  file_path: "/config/gcode/benchy.gcode"
  start_print: true
  level_before_print: true
```

## Status Values

The `sensor.flashforge_status` entity reports the following states:

Status | Description
-- | --
`READY` | Printer is idle and ready
`BUILDING_FROM_SD` | Actively printing from SD/internal storage
`BUILDING_COMPLETED` | Print has finished successfully
`BUSY` | Printer is busy (heating, leveling, etc.)
`PAUSED` | Print is paused
`BUILDING` | Generic printing state

See the [Status Values Wiki](../../wiki/Status-Values) for complete details.

## Example Automations

### Print Complete Notification
```yaml
automation:
  - alias: "Print Complete Notification"
    trigger:
      - platform: state
        entity_id: sensor.flashforge_status
        to: "BUILDING_COMPLETED"
    action:
      - service: notify.mobile_app
        data:
          title: "Print Complete!"
          message: "Your 3D print has finished"
          data:
            image: /api/image_proxy/image.flashforge_print_thumbnail
```

### Auto-Enable Filtration During Print
```yaml
automation:
  - alias: "Enable Filtration During Print"
    trigger:
      - platform: state
        entity_id: sensor.flashforge_status
        to: "BUILDING_FROM_SD"
    action:
      - service: fan.turn_on
        target:
          entity_id: fan.flashforge_external_filtration
  
  - alias: "Disable Filtration After Print"
    trigger:
      - platform: state
        entity_id: sensor.flashforge_status
        to: "BUILDING_COMPLETED"
    action:
      - service: fan.turn_off
        target:
          entity_id: fan.flashforge_external_filtration
```

### Door Open Alert During Print
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
        state: "BUILDING_FROM_SD"
    action:
      - service: notify.mobile_app
        data:
          title: "Warning!"
          message: "Printer door opened during print"
```

## Troubleshooting

### Printer Not Discovered
1. Ensure printer is powered on and connected to network
1. Verify Home Assistant and printer are on same network/VLAN
1. Try manual configuration with IP address

### Missing Entities
- **Filtration fans**: Only available on 5M Pro models
- **Thumbnails**: Only appear when actively printing with embedded thumbnail in G-code
- **Door sensor**: Requires door sensor hardware

### Connection Issues
1. Verify IP address hasn't changed (recommend DHCP reservation)
1. Check firewall allows ports 8898 and 8899
1. Ensure no other software is connected to printer

## Supported Models

This integration is tested with:
- FlashForge Adventurer 5M Pro
- Other FlashForge models may work but features vary

## Migration from v0.2.x

See the [Migration Guide](migration_guide.md) for detailed upgrade instructions.

## Contributing

Contributions are welcome! Please read the [Contribution guidelines](CONTRIBUTING.md)

## Support

- **Issues**: [GitHub Issues](https://github.com/joseffallman/hass_flashforge/issues)
- **Documentation**: [GitHub Wiki](https://github.com/joseffallman/hass_flashforge/wiki)
- **API Library**: [flashforge-python-api](https://github.com/GhostTypes/ff-5mp-api-py)

***

[flashforge]: https://github.com/joseffallman/hass_flashforge
[commits-shield]: https://img.shields.io/github/commit-activity/y/joseffallman/hass_flashforge.svg?style=for-the-badge
[commits]: https://github.com/joseffallman/hass_flashforge/commits/main
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/joseffallman/hass_flashforge.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/joseffallman/hass_flashforge.svg?style=for-the-badge
[releases]: https://github.com/joseffallman/hass_flashforge/releases
