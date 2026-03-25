# hacktiv8
<sub>(formerly A5_Bypass_OSS)</sub>

hacktiv8 is an open-source research project focused on analyzing and experimenting with iOS activation proccess using itunesstored sandbox escape vulnerability. It provides a one-click cross-platform solution for bypassing Activation Lock on legacy iOS devices without the need of pwning.

## Disclaimer

This project is intended strictly for research and educational purposes.  
It is not designed for, and must not be used in, production environments or for unlawful activities.  
The authors and contributors take no responsibility for any misuse or damage caused to devices, data, or systems.

## Requirements

The target device must be connected to Wi-Fi at all times during operation.  
Network connectivity is mandatory for the application workflow to function correctly.

## Compatibility

The tool is compatible with all A5 and A6 devices running **iOS 10.3.4**, **iOS 10.3.3**, **iOS 9.3.6**, **iOS 9.3.5**, and **Wi-Fi** devices running **iOS 8.4.1**.  

## Backend Configuration

The backend URL is stored in the `BACKEND_URL` global constant of [`main.py`](https://github.com/overcast302/A5_Bypass_OSS/blob/main/main.py)

Due to legacy iOS devices lacking trust for modern certificate authorities, the backend must either use HTTP, or serve an SSL certificate that chains to a root CA trusted by legacy iOS. Modern certificate authorities such as Let's Encrypt are not trusted on legacy iOS versions and will cause HTTPS connections to fail on target devices.

## Credits
- [pkkf5673](https://github.com/bablaerrr)
- [bl_sbx](https://github.com/hanakim3945/bl_sbx)
- [pymobiledevice3](https://github.com/doronz88/pymobiledevice3)

## License

Refer to the repository license file for licensing details.
