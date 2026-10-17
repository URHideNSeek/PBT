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

## Perched duration, payload envelope and relocation

Perched time is 1–720 hours (30 days). It is independent of flight time. The mission graph uses initial hop/return range on X and maximum mission payload mass on Y at selected flight-ready mass. Payload includes chosen mission sensing equipment plus unpowered additional payload; required flight/perching hardware is excluded from payload and remains in platform allocations. The solver allocates leftover gross mass to battery, preserving 20–75% battery-fraction bounds and checking energy, thrust and battery power. Added powered payload must declare its extra load. Selected boundary points feed the engineering BOM, including an explicit extra-payload row.

The desired recharge deadline is removed from mission controls and the envelope filter. Recharge time needed for relocation is computed after the selected perched period from net solar (weather-weighted harvest minus continuing sensing/communications load). The relocation hop equals the initial insertion distance. An outward, collinear hop is assumed: the next site's protected return distance is initial distance plus relocation distance (twice the initial hop). Departure energy covers release/approach/transition, relocation, the next site's return, the Wh landing reserve and analysis SOC floor. This route assumption is explicit; different geometry needs its own route model.

Arrival and the entire perched interval must preserve energy for an immediate current-site return. Later solar cannot repair a shortfall at arrival. The model flags durations that cross protected energy and derives a maximum allowable perched duration when the average net station balance is negative. Recovery does not borrow energy from a future recharge. Zero relocation recharge hours means already energy-ready; a missing result means capacity, net solar or protected return is insufficient. Charge limits/nighttime/weather sequencing remain outside the averaged trade model. Thirty-day persistence is not a zero-solar requirement.

## Operating-state power and two-line mass plot

Installed hardware is not continuously active. The secured baseline assumes a low-power Tier 1 monitor/housekeeping budget of 1W, payload computer sleep 0.05W, flight controller sleep 0.02W, GNSS standby 0.01W and combined communications standby 0.02W, plus sensor active/sleep duty. These are design assumptions requiring measured power-state and wake-interface evidence. A dedicated low-power monitor receives 10% of the compute mass allocation; payload compute changes from 65% to 55%, keeping total compute mass constant.

Scheduled communications check-ins/day × minutes/check-in directly sets scheduled radio awake time. Configured anomaly reports contribute their own awake minutes even when scheduled check-ins are zero. Tier 2 minutes/day directly sets selected Tier 2 sensor and compute wake time. Active radio energy is incremental above counted standby. Payload-computer wake energy is included for Tier 2 and communications; statistically independent overlapping windows are assumed so the same processor is not charged twice. Heavy imaging/RF/radar sensors in Tier 1 keep compute awake at the Tier 1 duty. GNSS selected for stationary sensing incurs its active power in addition to the standby allowance. Rail switching, low-power access to flight sensors, wake latency/overheads and shared-host firmware must be verified.

Daily load = Tier1-and-standby W ×24 + Tier2 incremental W × Tier2 min/day /60 + communications incremental W × total communications min/day /60. Sleep/report mission energy is separate. Solar net recharge is weather-weighted battery-delivered harvest minus the entire continuing daily load. Time to 100% is computed both from arrival and as additional waiting after the selected perched duration, using temperature/aging-adjusted capacity and retaining the protected return-energy gate. A negative/zero net balance cannot refill a depleted battery; full-charge spill is discarded. Charging taper, battery-temperature charge prohibitions and day/night sequencing are not modeled.

The mission graph shows payload mass and total aircraft mass against range, both in lb on one axis. Total aircraft mass remains the selected flight-ready mass while payload and battery trade within it. Infeasible ranges show neither line. An additional powered payload requires additional power entered in the model.

## Metric presentation
All mission controls, chart axes, engineering tables and downloadable trade/BOM outputs use metric units: kg/g, km/m/mm, m/s, N, N m and Celsius. Electrical energy remains Wh. The validated solver retains its existing private unit conventions behind an explicit conversion boundary; converted exports name their units. The startup point preserves the prior physical mass and distance (5.44310844 kg and 0.804672 km).

## Payload drives aircraft sizing
The initial mass slider selects total mission payload from 0 to 6 lb (0 to 2.72155422 kg), including the selected sensors. Aircraft mass and battery mass are driven outputs, not slider inputs. A battery-mass scan with local refinement finds the lightest closing allocation within the configured aircraft, thrust, peak/continuous power and mission-energy limits. The range graph holds payload fixed and recalculates total aircraft mass at each range. Payload below selected sensor mass is infeasible; extra unpowered payload is a separate BOM row. Default payload is 0.060 kg, matching the initial installed mission sensors. No battery-fraction driving slider remains.

## Flight and chronological perched-state model (October 14, 2026)

Flight propulsion now lives in flight.py. Induced, blade-profile and parasite terms vary with true airspeed, density, mass and rotor area. A fixed reference-density calibration anchors the propulsion model to the existing reference cruise power; it does not recalibrate to the current density. Active flight electronics are additive and excluded from the perched baseline. Profile fraction, reference rotor tip speed and density are editable assumptions. Thrust/RPM remains a static coefficient estimate; no matched motor/ESC/prop dataset or airframe flight-test validation is claimed.

perched.py tracks net DC-bus energy in five-minute intervals, with a 06:00–18:00 daylight profile and zero night harvest. The good/bad-day selector sets average daytime yield; the simulation does not generate actual sequences of cloudy days. Daily Tier 1, Tier 2 and communications energy retain their separate accounting and are distributed over each day. Exact burst timing remains unmodeled. Solar supplies concurrent loads before surplus is charged; net charging observes power and efficiency limits. Capacity clipping rejects excess energy. Pack-temperature limits disable charging outside the assumed battery charging temperature range; cell thermal transients and charging taper remain unmodeled.

mission.py composes insertion, perched consumption/solar, retrieval, and a protected contingency reserve. The reserve is a constraint, not an energy-consuming activity. Capacity sizing accounts for arrival readiness, overnight drawdown and saturation, not just average daily balance. Recharge/relocation readiness searches forward through the same daylight profile for up to 30 days and rejects crossing the existing return-energy boundary. Results beyond that search horizon are not declared impossible. The mission view exposes state energy accounting and the perched battery/return-reserve history.

The payload-driven minimum-battery scan continues to check continuous/peak power and thrust as well as mission energy. Shorter range may leave battery mass unchanged when peak-power capability governs. The search grid/local refinement is preliminary inverse sizing, not a globally certified optimizer.

Primary sources:
- Gao et al., Energy Model for UAV Communications: Experimental Validation and Model Generalization (2020), https://arxiv.org/html/2005.01305v1
- Zeng, Xu and Zhang, Energy Minimization for Wireless Communication with Rotary-Wing UAV, https://arxiv.org/abs/1804.02238
- UIUC folding propeller measurements, https://m-selig.ae.illinois.edu/props/volume-3/propDB-volume-3.html
- PX4 battery estimation, https://docs.px4.io/main/en/config/battery
- Solar and battery time-series modeling, https://samrepo.nlr.gov/help/battery_storage.html

This section supersedes earlier statements describing average continuous harvest or charging time calculated solely as deficit / average daily surplus.

## Three energy handoffs: symmetric-leg baseline
The mission baseline now mirrors insertion energy for recovery, at the same aircraft mass, distance and flight conditions. A default relocation hop has the insertion distance and the same complete-leg transition allowance. Recovery from the new perch is one leg, not the former outward-hop distance of two legs.

- Persist entry = departure battery energy minus complete insertion-leg energy, before the separate sensor-node wake/report allowance.
- Recovery-ready threshold = one complete leg + contingency reserve + battery minimum.
- Same-distance hop-ready threshold = two complete legs + contingency reserve + battery minimum.

Contingency and battery minimum are included once in each threshold. They are protected constraints, not loads to consume. The app displays all three Wh handoffs and the first hop-ready time from arrival; the existing relocation recharge output remains additional wait after the requested perched interval. Sensor and communications schedules continue during charging. Automatic sensor shutdown to prioritize charging is not assumed.

The symmetric baseline intentionally gives no reciprocal tailwind credit: recovery uses the insertion-leg conditions. Programmatic route overrides can set symmetric_legs=False and next_return_mi for unequal conditions/distances. Reposition distance can also be supplied independently. Chronological daytime/night charging, capacity and temperature limits, and recovery protection still apply. This section supersedes the earlier outward/collinear relocation assumption.

## First-tab display: Flight then Persist
The Mission & Envelope tab now presents Flight first: payload, calculated aircraft/battery mass, insertion flight-time estimate, complete-leg energy and energy handed to Persist, followed by the range/mass envelope. Persist follows with the requested duration, supported duration from that actual arrival-energy state, end energy, solar/load balance, visible battery/return-reserve history and readiness handoffs.

Supported Persist duration is a forward evaluation of the resulting aircraft configuration, not a second battery-sizing pass. It ends before the recovery threshold is crossed and searches 720 hours; reaching the horizon is displayed as at least 30 days rather than unlimited endurance. The existing requested perched-duration input still participates in aircraft sizing. Insertion time includes cruise and allocated approach/hover time; separate climb/transformation durations are not yet timed. Derived duration/time fields are included in current-mission exports.

## Elevation MSL and derived density altitude
The initial selectors include site elevation from -500 to 5,000 metres above mean sea level, with feet shown alongside. atmosphere.py uses tropospheric ISA pressure at that elevation and the hottest selected operating temperature to calculate dry-air density. It inverts the standard density profile to display density altitude as a separate derived equivalent altitude. Temperature remains the selected actual ambient temperature; it is not reduced a second time by an altitude lapse rate. Measured weather pressure and humidity are not modeled.

Derived density replaces the formerly independent air-density input and flows through flight propulsion, battery/aircraft sizing, engineering RPM/tip-speed estimates and envelope recalculation. Atmospheric assumptions are included in current-mission and sizing exports. Fixed scenario thrust/power limits remain allocations requiring qualification at those conditions. Elevation of a particular flight route above the site is not added automatically; use the representative flight elevation MSL for this preliminary study.

FAA terminology reference: https://www.faa.gov/sites/faa.gov/files/13_phak_ch11.pdf

## Flight-only sizing and 24-hour sensor-node policy
Aircraft/battery sizing now uses insertion and recovery energy, flight peak/continuous power, payload/hardware/reserves and a fixed 1 Wh handoff allowance. It ignores requested perched duration, solar mix, Tier 1/Tier 2 power/time and check-in count. Those selections are evaluated afterward against the fixed flight-sized battery. Physical sensor mass remains part of payload. This supersedes the former joint flight/Persist battery sizing.

Only recovery energy plus contingency and battery minimum is protected; hop energy is an unprotected readiness indication. Sensor-node policy compares the requested combined 24-hour Tier 1, Tier 2 and communications demand (including allocated housekeeping) with good-day harvest after array, net charging power, efficiency and charging-temperature constraints. A strictly positive good-day balance is required for sustainable continuous activity. An unsustainable node begins in sleep, then may wake once its actual battery energy exceeds the restart threshold; initial energy already above that threshold allows immediate wake. The chronological selected solar mix governs subsequent charge/discharge.

Sleep suspends scheduled sensing/communications and retains an editable low-power monitor (default 0.2 W). Default sleep entry is recovery protection +3 Wh; restart is protection +5 Wh. Both margins are editable; restart must exceed sleep margin. Awake operation also sleeps before the next step would cross the sleep boundary. If sleep itself cannot preserve recovery energy, the simulation stops at recovery-required rather than borrowing the reserve. A threshold above pack capacity prevents wake and is flagged. The model does not assume sleep is power-free or guarantee persistent operation with zero harvest.

Five-minute state transitions and per-day averaged activity loads remain approximations. Actual consumed energy, sleep hours, and a labelled active/sleep trace are reported. Requested activity cannot be claimed delivered while sleeping. Displayed continuous-load battery estimates are diagnostic only, not sizing drivers. Recharge/hop readiness forecasts use the same sleep/wake policy. Raw mission.size calls retain an explicit unmanaged-analysis option; the app and payload sizing use managed sleep.

## October 16: range/payload failure investigation and remedy
Reproduced the reported 0.500/0.550 kg payload and 8.2 km per-leg selections. The previous main view silently initialized 20 kt (10.29 m/s) planning wind inside the Engineering Sizing expander. Because the agreed baseline mirrors complete insertion-leg energy for recovery, it also mirrors the headwind energy. Combined with fixed hardware mass, battery derating, SOC floor, contingency and the 20 lb aircraft limit, this case has no feasible battery allocation. This is a genuine limitation of that assumed scenario, not a Persist-load or hop-reserve constraint.

The main mission panel now has an explicit Planning headwind selector in m/s with kt alongside. New sessions/reset start at 0 m/s for the nominal still-air case; adverse wind is an explicit trade. Existing payload/range selections are not reset. The symmetric-leg assumption is stated next to the control; no reciprocal tailwind credit is silently substituted and no mass, power, SOC or reserve limits are loosened. The advanced legacy exercise retains its separately visible scenario wind parameters.

Flight failures now use the same flight-input preparation and constraint checks as the sizing search. Diagnostics sample battery allocations within the existing mass limit, identify failed checks, and show usable/required energy, margin, sample mass and wind. Diagnostic samples are not presented as viable designs. The flight envelope and all previously rendered Engineering Sizing controls remain available on failure; Persist and BOM output are withheld rather than fabricated. The erroneous instruction to adjust perched duration for a flight-sizing failure is removed. Diagnostics are downloadable.

A 1e-9 kg comparison tolerance removes roundoff-only structure-allocation failures; it is not a physical mass allowance. Regression tests cover both screenshot payloads in still air, failure classification under 20 kt planning headwind, unchanged energy accounting, and recovering from a failed selection without resetting the app. Propulsion calibration remains provisional pending matched test data.

## Candidate research and screening (2026-10-16)

The catalog now includes 52 entries covering every sourced BOM category, including optional mission sensors. Each entry retains its own source-check date. New entries distinguish complete product candidates, prototype boards, component ICs, partial assemblies, and product-family sourcing leads. A family or IC is not an installed COTS replacement.

The BOM tab displays up to three fully documented specification matches and three potential candidates per row. The detail expander contains every researched candidate, its published attributes, outstanding verification, manufacturer source, and compliance evidence. The JSON export includes these classifications and all reasons.

- Specification match: all allocated checks and applicable sourcing evidence are documented; this does not constitute aircraft approval.
- Candidate — verification needed: no documented mismatch, but specifications, integration tests, requirements, or compliance evidence remain open.
- Excluded: at least one known specification or selected sourcing-policy mismatch, even when other data is missing.
- Not researched yet: no catalog entries for that category.

Strict sourcing never promotes missing NDAA or model-specific Blue evidence to a match. Explicitly false compliance is excluded under that policy. A complete antenna set, solar array, power distribution system, matched folding propulsion system, and battery/BMS assembly still require integration work. Candidate mass is not substituted into the mass model automatically; the table retains engineering allocations. Prices, stock and lead times are not yet maintained.

## Sensor roles and phase-specific communications (2026-10-17)

The perch camera is dedicated to landing. It remains required installed flight/perch hardware, is powered off while secured, and cannot be allocated to Tier 1 or Tier 2. A separate optional Visual ISR camera has its own editable payload mass, sensing power, encoded data rate, interface, and imaging parameters. It may serve either or both tiers; one installed camera is counted once. Prior navigation-camera tier selections are cleared once when migrating to these explicit roles. The startup configuration leaves the optional visual ISR camera off to retain the 60 g payload case.

The communications matrix has RF/mesh, cellular, and satcom rows, with Mission prep, Flight/perching, Passive ISR (Tier 1), and Active ISR (Tier 2) columns. A channel selected in any phase is installed once with its allocated antenna/feed mass. Removing all selections for a channel removes that modem and antenna allocation from flight mass and its BOM row. The remaining BOM rows show enabled phases. A prep-only selection still represents onboard hardware used during prep; external operator equipment is outside this aircraft BOM.

Each channel has editable modem mass, antenna/feed mass, active/standby power, and supply rail assumptions. These are planning allocations, not validated product figures. The initial RF/cellular/satcom active powers are 8/5/15 W, respectively; replace them with the installed product measurements. Default communications mass remains 870 g when all three channels are installed, including 261 g antenna/feed allowance.

Selected flight channels are continuously active during the modeled complete flight leg and their power is added to core flight electronics. Unselected flight channels are power-gated. Mission-prep energy is assumed externally supplied before the 95% departure SOC gate. Passive ISR selections service scheduled check-ins at the entered count and minutes per check-in; Active ISR selections service anomaly-report windows at the entered count and duration. These links do not transmit for the full Tier 2 sensing interval automatically. A phase with no selected channel produces no reports or report energy for that phase; data is retained onboard subject to configured storage capacity. Reporting policy does not alter sensor-tier definitions.

Multiple selected links are conservatively counted concurrently during each report window, rather than modeled as automatic failover. Perched-enabled channels retain standby draw between report windows. Separate scheduled and anomaly energy totals include payload-compute wake power. Their minute-weighted equivalent incremental power is passed to the existing chronological model, preserving the summed daily Wh. The engine still distributes report activity over the day; precise bursts, link acquisition, service coverage, and hardware power-gating require verification. Zero scheduled check-ins still permits anomaly reporting when an Active ISR channel is selected. No hop reserve is introduced.
