# Printer Status Values

The `sensor.flashforge_status` entity reports the current state of your FlashForge 3D printer. Understanding these status values is essential for creating automations and monitoring your prints.

## Machine Status Overview

The `sensor.flashforge_status` entity reports one of these `MachineStatus` values:

| Status | Description | Common Scenarios |
|--------|-------------|------------------|
| `READY` | Printer is idle and ready to accept commands | No active job, printer powered on and initialized |
| `BUILDING_FROM_SD` | Actively printing from internal storage | Print job in progress from SD card or internal memory |
| `BUILDING_COMPLETED` | Print has finished successfully | Print job completed, printer may still be cooling down |
| `BUSY` | Printer is performing an operation | Heating up, auto-leveling, homing, loading filament |
| `PAUSED` | Print job is paused | User paused print, or printer paused due to condition |
| `BUILDING` | Generic printing state | Alternative printing status (model-dependent) |
| `DEFAULT` | Unknown or unrecognized status | Fallback state when status cannot be determined |

## Move Mode Status

The printer also reports a `MoveMode` status that indicates the current movement state:

| Move Mode | Description | Common Scenarios |
|-----------|-------------|------------------|
| `READY` | Print head is stationary and ready | Printer idle, waiting for commands |
| `MOVING` | Print head is actively moving | During active printing, homing, or manual movement |
| `PAUSED` | Movement is paused | Print paused, waiting to resume |
| `WAIT_ON_TOOL` | Waiting for tool operation | Heating nozzle, loading filament, changing tools |
| `HOMING` | Performing homing operation | Executing G28 command, printer finding home position |
| `DEFAULT` | Unknown or unrecognized move mode | Fallback state when mode cannot be determined |

## Detailed Status Information

### READY
**Machine Status:** Idle
**Move Mode:** Ready
**LED Indicator:** Typically solid color (varies by model)

The printer is:
- Powered on and initialized
- Not performing any task
- Ready to accept new commands
- Not heating any components
- Print head stationary

**Use Cases:**
- Trigger notification that printer is available
- Automatically queue next print job
- Safe to perform maintenance operations

**Example Automation:**
```yaml
automation:
  - alias: "Printer Available Notification"
    trigger:
      - platform: state
        entity_id: sensor.flashforge_status
        to: "READY"
    action:
      - service: notify.mobile_app
        data:
          message: "3D Printer is ready for next job"
```

### BUILDING_FROM_SD
**Machine Status:** Printing
**Move Mode:** Moving
**LED Indicator:** Usually pulsing or animated

The printer is:
- Actively printing a file from internal storage
- Heating and maintaining temperatures
- Moving print head and bed
- Consuming filament
- Print head in motion

**Use Cases:**
- Enable air filtration
- Disable LED lights for night printing
- Monitor progress with notifications
- Track time remaining

**Example Automation:**
```yaml
automation:
  - alias: "Start Filtration When Printing"
    trigger:
      - platform: state
        entity_id: sensor.flashforge_status
        to: "BUILDING_FROM_SD"
    action:
      - service: fan.turn_on
        target:
          entity_id: fan.flashforge_external_filtration
```

### BUILDING_COMPLETED
**State:** Complete
**LED Indicator:** Typically solid or different color

The printer has:
- Finished the print job successfully
- May still be cooling down bed/nozzle
- Print is ready for removal
- May have returned to home position

**Use Cases:**
- Send completion notification
- Disable filtration
- Turn on LED for print removal
- Take completion photo

**Example Automation:**
```yaml
automation:
  - alias: "Print Complete Actions"
    trigger:
      - platform: state
        entity_id: sensor.flashforge_status
        to: "BUILDING_COMPLETED"
    action:
      - service: notify.mobile_app
        data:
          title: "Print Complete!"
          message: "{{ states('sensor.flashforge_file') }} has finished"
          data:
            image: /api/image_proxy/image.flashforge_print_thumbnail
      - service: fan.turn_off
        target:
          entity_id: fan.flashforge_external_filtration
      - service: light.turn_on
        target:
          entity_id: light.flashforge_light
```

### BUSY
**Machine Status:** Working
**Move Mode:** May vary (MOVING, WAIT_ON_TOOL, HOMING)
**LED Indicator:** May pulse or animate

The printer is:
- Performing preparatory operations
- Heating up to target temperatures
- Auto-leveling the bed (MoveMode: HOMING)
- Homing axes (MoveMode: HOMING)
- Loading or unloading filament (MoveMode: WAIT_ON_TOOL)
- Processing G-code commands

**Important:** The printer is not ready for new commands during this state.

**Move Mode Details:**
- `HOMING`: Executing homing sequence (G28)
- `WAIT_ON_TOOL`: Waiting for temperature or tool operation
- `MOVING`: Performing movement operations

**Use Cases:**
- Wait before sending additional commands
- Display "preparing" status on dashboard
- Track time to start actual printing

**Example Automation:**
```yaml
automation:
  - alias: "Heating Notification"
    trigger:
      - platform: state
        entity_id: sensor.flashforge_status
        to: "BUSY"
    condition:
      - condition: numeric_state
        entity_id: sensor.flashforge_bed_target_temp
        above: 0
    action:
      - service: notify.mobile_app
        data:
          message: "Printer heating up for print job"
```

### PAUSED
**Machine Status:** Paused
**Move Mode:** Paused
**LED Indicator:** Often pulsing slowly or specific pause color

The printer has:
- Paused the current print job
- Maintained temperatures (usually)
- Stopped filament extrusion
- May have moved print head to parking position
- Print head stationary

**Pause Reasons:**
- User manually paused
- Filament runout detected
- Door opened (if equipped)
- Other safety condition

**Use Cases:**
- Send alert about paused state
- Check why pause occurred
- Prompt user to resume or cancel

**Example Automation:**
```yaml
automation:
  - alias: "Print Paused Alert"
    trigger:
      - platform: state
        entity_id: sensor.flashforge_status
        to: "PAUSED"
    action:
      - service: notify.mobile_app
        data:
          title: "Print Paused"
          message: "Print job has been paused"
          data:
            actions:
              - action: "RESUME_PRINT"
                title: "Resume"
              - action: "CANCEL_PRINT"
                title: "Cancel"
```

### BUILDING
**State:** Printing (Alternative)
**LED Indicator:** Similar to BUILDING_FROM_SD

Some printer models or firmware versions report a generic `BUILDING` status instead of `BUILDING_FROM_SD`. This indicates:
- Actively printing
- Same behavior as BUILDING_FROM_SD
- Model or firmware variation

**Note:** Create automations that handle both `BUILDING_FROM_SD` and `BUILDING` for maximum compatibility.

**Example Automation:**
```yaml
automation:
  - alias: "Printing Status Handler"
    trigger:
      - platform: state
        entity_id: sensor.flashforge_status
        to:
          - "BUILDING_FROM_SD"
          - "BUILDING"
    action:
      - service: script.start_print_monitoring
```

## Status Transitions

### Normal Print Flow
```
READY → BUSY → BUILDING_FROM_SD → BUILDING_COMPLETED → READY
```

### Paused Print Flow
```
BUILDING_FROM_SD → PAUSED → BUILDING_FROM_SD → BUILDING_COMPLETED
```

### Print Cancellation
```
BUILDING_FROM_SD → BUSY → READY
```

## Using Status in Automations

### Multi-Status Conditions
```yaml
condition:
  - condition: state
    entity_id: sensor.flashforge_status
    state:
      - "BUILDING_FROM_SD"
      - "BUILDING"
      - "BUSY"
```

### Status Change Detection
```yaml
trigger:
  - platform: state
    entity_id: sensor.flashforge_status
    from: "BUILDING_FROM_SD"
    to: "BUILDING_COMPLETED"
```

### Long-Running Print Alert
```yaml
automation:
  - alias: "Long Print Alert"
    trigger:
      - platform: state
        entity_id: sensor.flashforge_status
        to: "BUILDING_FROM_SD"
        for:
          hours: 4
    action:
      - service: notify.mobile_app
        data:
          message: "Print has been running for 4 hours"
```

## Dashboard Display

### Using Status in Cards

**Conditional Card:**
```yaml
type: conditional
conditions:
  - entity: sensor.flashforge_status
    state: "BUILDING_FROM_SD"
card:
  type: entities
  entities:
    - sensor.flashforge_job_percentage
    - sensor.flashforge_print_time_remaining
    - sensor.flashforge_current_layer
```

**Status Badge:**
```yaml
type: entity
entity: sensor.flashforge_status
name: Printer Status
icon: mdi:printer-3d
```

**Custom Status Colors:**
```yaml
type: entity
entity: sensor.flashforge_status
card_mod:
  style: |
    :host {
      {% if is_state('sensor.flashforge_status', 'BUILDING_FROM_SD') %}
        --paper-item-icon-color: orange;
      {% elif is_state('sensor.flashforge_status', 'BUILDING_COMPLETED') %}
        --paper-item-icon-color: green;
      {% elif is_state('sensor.flashforge_status', 'PAUSED') %}
        --paper-item-icon-color: red;
      {% else %}
        --paper-item-icon-color: grey;
      {% endif %}
    }
```

## Troubleshooting

### Status Not Updating
1. Check integration is connected (Configuration → Integrations)
1. Verify printer is on and network accessible
1. Check Home Assistant logs for errors
1. Restart integration or Home Assistant

### Unknown Status Values
Some printer models may report different status strings. If you encounter an unknown status:
1. Note the exact status string in Home Assistant Developer Tools → States
1. Report it on the GitHub issues page
1. The integration may need updating for new models

### Status Stuck
If status appears frozen:
1. Reload the integration
1. Check printer network connection
1. Power cycle the printer if necessary
1. Verify polling is working (check coordinator logs)

## Model-Specific Notes

### FlashForge Adventurer 5M Pro
- Uses `BUILDING_FROM_SD` for internal storage prints
- Supports all standard status values
- Status updates every 30 seconds during polling

### Other Models
Status values and behavior may vary by model and firmware version. The integration attempts to normalize these values for consistency.

## Additional Status Information

Beyond the main machine status, the printer reports several additional state flags:

### Endstop Status

The printer's endstops (limit switches) indicate when axes have reached their boundaries:

| Endstop | Description |
|---------|-------------|
| `X-max` | X-axis maximum position switch (0=not triggered, 1=triggered) |
| `Y-max` | Y-axis maximum position switch (0=not triggered, 1=triggered) |
| `Z-min` | Z-axis minimum position switch (0=not triggered, 1=triggered) |

### Status Flags (S, L, J, F)

These low-level status flags provide additional printer state information:

- **S Flag**: General status indicator
- **L Flag**: Layer-related status
- **J Flag**: Job-related status
- **F Flag**: Filament-related status

*Note: The exact meaning of these flags may vary by printer model and firmware version.*

### LED Status

Indicates whether the printer's built-in LED lights are currently on or off:
- `1`: LEDs are on
- `0`: LEDs are off

### Current File

The name of the currently loaded or printing G-code file, or empty if no file is loaded.

## Accessing Extended Status Information

These extended status values are available through the TCP API's `M119` command (EndstopStatus):

```python
from flashforge import FlashForgeClient

async with FlashForgeClient(ip, serial, check_code) as client:
    await client.initialize()

    # Get extended status via TCP
    endstop_status = await client.tcp_client.get_endstop_status()

    if endstop_status:
        print(f"Machine Status: {endstop_status.machine_status.value}")
        print(f"Move Mode: {endstop_status.move_mode.value}")
        print(f"LED Enabled: {endstop_status.led_enabled}")
        print(f"Current File: {endstop_status.current_file}")

        if endstop_status.endstop:
            print(f"Endstops - X:{endstop_status.endstop.x_max} "
                  f"Y:{endstop_status.endstop.y_max} Z:{endstop_status.endstop.z_min}")
```

Status monitoring works best when combined with:
- `sensor.flashforge_job_percentage` - Print progress
- `sensor.flashforge_print_time_remaining` - Time left
- `binary_sensor.flashforge_door` - Door state
- `sensor.flashforge_bed_temp` - Bed temperature

## Additional Resources

- [Home Assistant Template Documentation](https://www.home-assistant.io/docs/configuration/templating/)
- [Automation Triggers](https://www.home-assistant.io/docs/automation/trigger/)
- [GitHub Repository](https://github.com/joseffallman/hass_flashforge)
