# Valve Index Base Station Integration for Home Assistant

This integration adds support for Valve Index Base Stations to Home Assistant, including auto-discovery.

Supported entities:

| Name     | Type     | Description                                |
|----------|----------|--------------------------------------------|
| Power    | `Switch` | Turn the Base Station on/off (awake/sleep) |
| Identify | `Button` | Cause the Base Station to blink            |
| Channel  | `Select` | Change the channel of the Base Station     |

## Usage

### Requirements

To use this integration you need to have some sort of Bluetooth adapter in your Home Assistant, see the [official documentation for details](https://www.home-assistant.io/integrations/bluetooth/).

### Installation

* Install HACS
* Manually add this repo
