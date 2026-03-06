A CLI/MCP dedicated to reverse-engineering and controlling Litter Robot devices

https://github.com/engageintellect/litterbot seems to have figured it out a couple years ago, but I want to be sure we have 100% coverage over the exposed interface (for both reading out metrics and sending commands). Ideally, this becomes a PM2 service which detects activity and forcibly resets + cycles upon the same debounced timing logic that's built in, but degrades over time as sensors and connections erode. Deep cleans momentarily restore functionality, but over time it always becomes unreliable once again and the space's smell suffers.

`ses_33b223eb2ffe5dScWW90lMjVrX`
