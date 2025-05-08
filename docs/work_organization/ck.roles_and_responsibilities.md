<!-- toc -->

- [Roles And Responsibilities](#roles-and-responsibilities)
  * [Setting and achieving Company goals](#setting-and-achieving-company-goals)
  * [Must-have vs nice-to-have goals](#must-have-vs-nice-to-have-goals)
    + [If must-have goal is slipping](#if-must-have-goal-is-slipping)
  * [Meisters](#meisters)
  * [List of functional teams](#list-of-functional-teams)
  * [Backtest](#backtest)
  * [List of meisters](#list-of-meisters)
    + [DataMeister](#datameister)
    + [AwsMeister](#awsmeister)
    + [AsanaMeister](#asanameister)
    + [SimulationMeister](#simulationmeister)
    + [BuildMeister](#buildmeister)
    + [ExperimentMeister](#experimentmeister)
    + [FeedbackMeister](#feedbackmeister)
    + [HiringMeister](#hiringmeister)
    + [IntegrationMeister](#integrationmeister)
    + [TradingMeister](#tradingmeister)

<!-- tocstop -->

# Roles And Responsibilities

## Setting and achieving Company goals

- The company has quarterly high-level goals
  - These goals are broken in short term goals (e.g., 1-2-3 weeks) and 2 months
    goals
  - Each goal is described in terms of a complete list of Projects in the
    IssueSpecs gdocs
  - Each Project is estimated in length (with or without a detailed list of
    Issues)
    - E.g.,
      ```
      Implement XYZ
      Features:
        ...
      Code = 2 weeks
      Debug = 1 week
      Deployment = 1 week
      ```
    -
    - The purpose is to have a way to track dependencies and have a way to
      measure critical path
    -
- Each Project needs to be completely described in Issues when we start working
  on it

## Must-have vs nice-to-have goals

- There are must-have and nice-to-have goals
  - E.g., must-have is "trade for 8 hours in TomG's account by April 15"
  - E.g., nice-to-have projects are paying tech debts, improving interfaces,
    documentation
- Teams should be focused on achieving must-have goals by their ETAs and
  prioritize must-have vs nice-to-have goals
  - Nice-to-have goals should be executed when there are free time/resources

### If must-have goal is slipping

- If a milestone is slipping, we don't simply move everything forward but we
  descope, cut corners, add hacks, reprioritize the milestones
  - The goal is to achieve the must-have goal even if it is in a simplified form
  - If a must-have is slipping we pause some nice-to-have effort and repurpose
    the team members
- During Monday's Company meeting we review the weekly progress towards the
  milestones
  - TODO(gp): We need to keep a Gantt diagram to maintain the

## Meisters

- Meisters are in charge of maintaining orderly and timely execution of services
  and functions
  - They are not necessarily the developers of the systems they monitor and run,
    but they are mainly users and supervisors
  - Each team should have some sort of redundancy in executing the meister
    processes
  - Processes should be documented

- We separate the development vs the meistering of subsystems on purpose
  - We want to assign these responsibilities in a "redundant way"
  - E.g., we have one team develops and another using the tools, so we have some
    redundancy and we force teams to document in order to talk to each other

## List of functional teams

- TradingOps
  - Grisha
- TradingInfra
  - Juraj
  - DataMeister
- ## Backtest

## List of meisters

### DataMeister

- Previously known as AirflowMeister
- Monitor all the Airflow jobs related to on-boarding data

### AwsMeister

- Monitor all the IT infrastructure (including Airflow infra)

### AsanaMeister

- Ensure tasks in Asana are executed on time

### SimulationMeister

- Run Backtesting experiments
  - Catalog backtests
  - Perform sweeps for tuning
    - Optimizer parameters
    - Prices from simulated delay
- Execution shortfall investigation
  - Compare results of live trading to backtests
  - Compare execution shortfall to ideal and modeled execution shortfall

### BuildMeister

- Ensure builds are green
- More info at docs/work_organization/all.buildmeister.how_to_guide.md

### ExperimentMeister

- Runs, summarizes,
- Live experiments

### FeedbackMeister

### HiringMeister

### IntegrationMeister

### TradingMeister

- Owns
  - Scheduled trading
  - Shadow trading
  - System reconciliations

- Scheduled trading operations
  - Ensure smooth operation of regularly scheduled pipelines (e.g., C11a config1
    in a TomG account)
  - Monitor account balances
    - We should have a notebook approach like the Buildmeister to monitor
      current positions, balance, and other metrics (e.g., how much was traded)
  - Monitor system performance (e.g., dataflow latency, data latency, memory
    usage)
    - TODO(gp): These info should be collected in a dashboard somehow
  - Maintain detailed logs
  - Analyze reconciliation results
  - Summarize highlights in a brief, daily email

- Shadow trading
  - Ensure 24/7 operation of shadow trading pipelines
  - Stitch daily runs together weekly for a weekly summary
  - Perform weekly reconciliation runs
  - Shadow trading should always be a superset of scheduled trading configs

The rotation is here
https://docs.google.com/spreadsheets/d/12OhDW4hzSLekorrri2WfRkV8h3JcnB8WQd1JEL_n0D8/edit
