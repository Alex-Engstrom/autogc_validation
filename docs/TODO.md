# To Do
## Misc
- [x] Add n-pentane == 0 check to the notebook generator and other calibrants
- [x] Add upper_cal_limit variable to each week in the notebook generator function.
- [x] Add prior and next prec to flag range generator
- [] Add calibration dataclass and database table
- [x] Add in "ususal suspects" to qualifier generation code
- [x] MAke sure nulled hours are entered in qualifer generator and qc review code
- [x] Revise MDVR template to have appropriate print area for pdf conversion
- [x] Add outlier detector to review (monthly outlier and vs month last year)
- [x] Add AQS file vs dataset check function
- [x] Add distribution plotting function and outlier review
- [x] Revise RT screening to return outliers which are above mdl
- [x] Revise monthly notebook so that qualifiers and nulls can be entered there and compared to the resulting AQS file.

- [x] Add "mdl_sum = mdl_failures.iloc[:,1:].sum(axis=0)
mdl_sum_text = [f"{aqs_to_name(col).lower()} ({count} exceedances)" for col, count in mdl_sum.items() if count > 1]"
to notebook generator.
- [x] Add small function to add the current month to the MDVR document
- [] Add small function to add QC canister info the the MDVR doc.
- [] Fix cells in MDVR template
- [] Add plots folder to monthly folder 
- [x] Clean up anaconda environments
- [] Correct blank screening function so TNMHC isnt included in compounds above 0.5 ppbC
- [x] Update how code calculates which hour data belongs to to match MAX
    - [x] Update this in AQS file comparison
- [] Add screening function for TNMTC vs TNMHC checks
- [] Add monthly review before AQS file check
- [x] Add sample hour-filename check to notebook template
- [x] Add long/short sampletype check to dataset class



## AQS upload file functions
- [x] Summarize nulls by hour
- [x] Summarize qualifiers by hour
- [x] Summarize nulls by code
- [x] Summarize qualifiers by code

## AutoGC Core
- [x] Connect to github
- [x] Write function to parse MAX crosstab csv files
- [x] Write function to parse MAX figure download csvs
- [] Move more stuff from gc_validation enums to here

## txt_parser
- [] Add crosstab comparison function