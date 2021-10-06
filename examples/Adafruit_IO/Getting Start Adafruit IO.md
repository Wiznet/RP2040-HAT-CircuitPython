# Getting Start Adafruit IO



## Introduction

> Adafruit IO is a system that makes data useful. Our focus is on ease of use, and allowing simple data connections with little programming required. IO includes client libraries that wrap our REST and MQTT APIs. IO is built on Ruby on Rails, and Node.js. Sources : [Adafruit IO Overview][link-adafruit_io]

![][link-logo]



## Start Adafruit IO





> ## Create an account at adafruit.com

Please refer to the following link to proceed with the subscription. Some services are free of charge.

1. Create an account - [io.adafruit.com to Sign up][link-sign up]

![][link-account]



2. Get the token( `ADAFRUIT_IO_USERNAME`, `ADAFRUIT_IO_KEY` ) you need to use Adafruit IO

![][link-menu]

![][link-token]



> ## Feed

Data continuously coming in from one sensor constitutes one **feed**. Feed includes various metadata such as timestamps, public or private, and other information. Only the core should be stated, **One feed should be created for each sensor.**

1. Make new Feed

![][link-feed_1]



2. Adjust Feed Characteristic

![][link-feed_2]



> ## Dashborads

A collection of instrument panels that can visually see the current status and continuous changes of the feed. **Up to 10 feeds** (in the free version)  and **up to 5 dashboards** (in the free version)  can be made. Multiple feed data can be placed on one dashboard.

1. Make a new Dashboard

![][link-dashboard_1]



2. Get the block that fits the feed and configure the UI on the dashboard. 

![][link-dashboard_2]



3. Output the collected data to the Dashboard and provide it to the user.

![][link-dashboard_3]





<!--
Link
-->



[link-adafruit_io]: https://learn.adafruit.com/welcome-to-adafruit-io/overview
[link-sign up]: https://accounts.adafruit.com/users/sign_in
[link-logo]: https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/Adaruit_io/Adafruit_logo.png
[link-account]: https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/Adaruit_io/account.png
[link-menu]: https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/Adaruit_io/Adafruit_menu.png
[link-token]: https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/Adaruit_io/Adafruit_token.png
[link-feed_1]: https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/Adaruit_io/Adafruit_feed_1.png
[link-feed_2]: https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/Adaruit_io/Adafruit_feed_2.png
[link-dashboard_1]: https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/Adaruit_io/Adafruit_dashboard_1.png
[link-dashboard_2]: https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/Adaruit_io/Adafruit_dashboard_2.png
[link-dashboard_3]: https://github.com/Wiznet/RP2040-HAT-CircuitPython/blob/master/images/Adaruit_io/Adafruit_dashboard_3.png