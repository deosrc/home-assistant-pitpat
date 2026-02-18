# Home Assistant PitPat Integration

This is a custom integration for Home Assistant to add support for the PitPat GPS tracker.

This is in no way endorsed or affiliated with PitPat.

> :warning: This integration is very experimental.
>
> - Expect bugs caused by limited testing causing unreliable or incorrect data (I only have access to a single device of one type)
> - Expect potentially breaking changes requiring you to re-write scripts and automations
> - Don’t expect support or quick fixes
> - A PitPat subscription isn’t required for any of the integration functionality. The integration in some ways is replicating some of the functionality of the pitpat subscription model. Expect it to disappear swiftly if PitPat decide they don’t like this being available and take action.

![Screenshot of the integration sensors](.media/Screenshot1.png)
![Screenshot of the integration sensors](.media/Screenshot2.png)

Some sensors may not be available for your device type. I only have a single GPS device tracker for testing.

## Setup

1. Add this as a custom repository via HACS
1. Install the integration:

    [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=deosrc&repository=home-assistant-pitpat&category=Integration)

1. Add the integration:

    [![Open your Home Assistant instance and show an integration.](https://my.home-assistant.io/badges/integration.svg)](https://my.home-assistant.io/redirect/integration/?domain=pitpat)

1. Enter the email address and password for your PitPat account.

If authentication fails later (e.g., password changed), Home Assistant will prompt you to re-authenticate. Click repair, and re-enter your PitPat credentials.

> :information_source: Previous versions required packet capture from the Android app. This is no longer required as of v0.5.

## Options

By default the integration polls for updates every 5 minutes. This can be increased in the options panel:

1. Go to the integration page:

    [![Open your Home Assistant instance and show an integration.](https://my.home-assistant.io/badges/integration.svg)](https://my.home-assistant.io/redirect/integration/?domain=pitpat)

1. Click the options cog for the entry.
1. Adjust the poll interval as required and save.

The new interval should take effect without needing to reload anything.

## Troubleshooting

As mentioned, this is highly experiment, and is a small hobby project. If you run into issues, please check the logs and try to diagnose the issue yourself. If you need to raise an issue, please include logs.

## How can I help?

- If your PCAP capture manages to decrypt the `auth.pitpat.com` requests, I would be very interested in seeing them (obviously with sensitive parts redacted).
- Any other investigation into workings of the APIs.
- Investigating any issues you encounter. My testing is fairly limited due to time and only having a single device.
- Reporting issues including any logs.
- Investigating any issues others post.

## Can I fork this?

Sure. I would just ask that you:

- Consider submitting your work as a pull request first,
- If you plan to fork this permanently, include a note to credit my work, and anyone else who has contributed.
