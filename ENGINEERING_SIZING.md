# Engineering Sizing

The app has two tabs: Mission & Envelope (driving capability choices) and Engineering Sizing (downstream design allocations and estimates). The latter does not generate independently approved requirements or stable requirement IDs.

Choose the current mission, a saved trade, or a calculated envelope point. Envelope point sizing uses the frozen assumptions of that plot. CSV/JSON exports include sizing results; mission selections and engineering assumptions remain distinguishable.

Outputs include gross and nonbattery mass, battery mass allocation, required nominal/usable Wh, required installed Wh/kg, Ah at assumed nominal voltage, required pack mass at assumed Wh/kg, disk area/loading in kg/m², N/m² and lb/ft², per-rotor hover/continuous thrust, estimated rotor RPM, tip speed, electrical power/current, propulsion mass allocation, battery W/kg and solar area/output.

Static RPM is estimated from T = CT rho (RPM/60)^2 D^4. CT is user-assumed, not calibrated. Direct drive is assumed. RPM is not a prop/hub safe-speed rating, motor operating guarantee, cruise estimate or acoustic prediction. Motor/ESC/prop curves are needed for selection. Electrical input power is distinct from shaft output power.

Pack Ah uses nominal voltage; current uses minimum loaded voltage. Adding the derived pack mass changes aircraft mass and requires a new integrated trade. Average-solar sizing retains the model's weather-sequence limitations. Saved trade sizing applies the current CT and nominal-voltage assumptions and identifies that explicitly.

44 local regression, interaction and sizing tests passed after the tab change, including selecting a saved scenario and an envelope boundary, RPM/coefficient scaling, thrust inversion, voltage/current accounting and all input boundaries. Existing CI runs these tests.
