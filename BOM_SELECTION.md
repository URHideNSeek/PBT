# Engineering BOM and COTS screening

Mission controls drive energy, flight power, propulsion thrust/current, temperature capacity and station duration. Engineering Sizing selects the installed sensing mix. BOM Options screens products against the resulting per-row requirements.

## Sensor scheduling

A device selected in either tier is installed once. Quantity is an explicit allocation. Tier 1 duty determines normal active/sleep power. Tier 2 replaces an idle interval with active operation, so a device already continuously active in Tier 1 adds no duplicate power or recorded data. A Tier-2-only device remains installed at zero Tier 2 minutes and consumes its entered sleep allowance. Logged Mbps is encoded/stored output, not raw sensor bus rate. GB use decimal units.

Sensor masses, active/sleep power, supply, interfaces and measurement criteria are editable planning allowances. Wideband RF and passive radar are separate from the communications radio; passive radar needs coherent reference/surveillance receivers. No detection range is inferred from tuning coverage. Payload computer throughput and perception/landing performance require workload benchmarks.

## Mass allocation

Battery uses the selected aircraft mass fraction. The envelope allocates remaining mass to battery after the selected fixed equipment and reserves. Propulsion, compute, communications and solar retain their baseline top-level allocations, subdivided without double counting:

| Allocation | Split |
|---|---|
| Propulsion | 65% motors; 12% four-channel ESC; 15% folding props/hubs; 8% mounts/hardware |
| Compute/navigation electronics | 10% flight controller; 65% payload computer; 10% storage; 15% navigation camera |
| Communications | 12% mesh radio; 12% cellular modem; 46% satcom; 30% antenna set |
| Solar | 72% array; 28% charger |
| Structure/mounting/mechanisms | 65% enclosure/mounting; 35% perch/transformation mechanism |

Separate editable reserves cover wires/connectors, fasteners, sealants/adhesives and growth. Additional allocations cover GNSS, actuators and power conversion/distribution. The shared sensor table puts locked Flight / perching before Tier 1 and Tier 2. Required IMU, compass, barometer, GNSS, navigation camera, distance, contact, latch-position and battery-health hardware is permanently installed. Tier checkboxes enable stationary collection on the same device; both unchecked leaves it available for flight/perching/protection. Host controller/GNSS/BMS mass is counted once. Distance/contact/latch sensors add a fixed 30 g installation allowance. Optional mission-only sensors add mass only when selected. Camera/range idle and additional stationary active power are accounted through the shared profile; controller/GNSS/BMS electronics baseline remains in housekeeping. Controller and field kit are outside aircraft takeoff mass.

The allocated BOM total plus unused headroom equals selected flight-ready mass; negative headroom fails mass closure. Assumptions do not establish manufacturing feasibility. Motor loads depend on total mass, including reserves.

## Screening

Each row includes quantity, per-unit/row mass, numeric/string constraints and unresolved requirements. The matching engine compares every required attribute, excludes absent evidence, refuses rows with unresolved critical requirements and shows at most three matches. It distinguishes mismatch, missing product data, compliance gaps and no catalog entry. Actual product mass is compared with the per-unit allocation; quantities multiply into installed BOM mass.

Controlled sourcing requires source-backed NDAA and exact-model Blue Framework evidence. Manufacturer declarations carry their source and are not independent aircraft certification. No manufacturer-wide or country-of-origin inference is made. Unrestricted sourcing simply removes those two gates and includes Chinese-market products; it is not a declaration that every shown product is legally noncompliant. Wires, fasteners, sealants, structure, mechanisms and growth are reserves, not product searches.

`catalog.json` is an offline curated snapshot of manufacturer/primary specifications checked October 14, 2026, not an exhaustive live market search. Unknown values are intentionally omitted. Datasheet headline rates/ranges and peak ratings are not promoted into installed/continuous guarantees. Blue/NDAA status is not inferred between generations. Procurement availability, model revision and full-system qualification still need confirmation. A row match never implies a complete integrated aircraft closes all budgets.

## Derived component criteria

- Battery: nominal Wh, nominal voltage tolerance, loaded/full-charge limits, continuous/burst current with margin, allocated mass and operating temperature. Required Wh uses selected solar and temperature assumptions. Pack performance/charging curves need verification.
- Motor/ESC/prop: thrust, per-rotor power, estimated RPM, diameter/folding constraint, test voltage, current margin, protocols, quantity and matched assembly evidence. Motor ratings alone do not establish thrust.
- Compute/navigation: RAM, required sensor interfaces, power/mass budget, GNSS accuracy/update rate, flight-controller outputs/protocols and navigation camera image requirements. Port bandwidth and workload benchmarks remain open.
- Storage: selected encoded sensor traffic × active schedules × retention × 1.25 margin; sustained write throughput separately uses concurrent encoded rate ×1.25. Gross radio I/Q is not silently equated to logged output.
- Communications: required application rate, route-derived installed range, selected band, six-node mesh, supply/power/mass/temperature. Carrier, satellite service and installed antenna/link budget require evidence.
- Solar/power: peak array power/packing area/diameter, MPPT and pack voltage, required converter rails and peak stationary output with current margin. Daily harvest remains an installed battery-delivered mission assumption.
- Actuators: count, supply, torque and PWM interface; mechanism geometry/travel/speed/current/holding loads require definition.
- Sensors: selected interface, rail, active/sleep allowances, mass, temperature and sensor-specific measurement limits; camera image size/frame rate, GNSS accuracy, RF tuning/bandwidth and passive radar coherence are explicit.

CSV/JSON exports retain requirements, allocations, selected configuration, source URLs, checked dates and rejected-candidate reasons. Saved trades and envelope-point sizing freeze their sensor plan/settings.

Required hardware is not a claim that the sensing suite alone proves autonomous perching. Detection/geometry, approach accuracy, secured-state verification, mechanism loads and integrated tests remain required. The flight/perching checkbox column is fixed; stationary-tier boxes are editable. Required-device quantity is one and incremental sensor mass is zero because its host BOM allocation already includes it. Measurement constraints from a shared sensor profile tighten the host row instead of creating another device.
