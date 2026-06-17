library(strucchange)
prices <- read.csv("C:/Time series research paper/Data/features.csv")

prices$Date <- as.Date(
  prices$Date,
  format = "%d-%m-%Y"
)
#Checking for AAPL break points
#Bao Perron test
bp_aapl <- breakpoints(
  roll_var_aapl ~ 1,
  data = prices
)

summary(bp_aapl)

plot(bp_aapl)
BIC(bp_aapl)

bp_aapl_3 <- breakpoints(
  roll_var_aapl ~ 1,
  data = prices,
  breaks = 3
)

bp_aapl_3$breakpoints

prices$Date[bp_aapl_3$breakpoints]

#Chow test
sctest(
  roll_var_aapl ~ 1,
  type = "Chow",
  point = bp_aapl_3$breakpoints[1],
  data = prices
)

sctest(
  roll_var_aapl ~ 1,
  type = "Chow",
  point = bp_aapl_3$breakpoints[2],
  data = prices
)

sctest(
  roll_var_aapl ~ 1,
  type = "Chow",
  point = bp_aapl_3$breakpoints[3],
  data = prices
)

#Checking for MSFT 
#Bao perron test
bp_msft <- breakpoints(
  roll_var_msft ~ 1,
  data = prices
)

summary(bp_msft)

plot(bp_msft)
BIC(bp_msft)

bp_msft_2 <- breakpoints(
  roll_var_msft ~ 1,
  data = prices,
  breaks = 2
)

bp_msft_2$breakpoints

prices$Date[bp_msft_2$breakpoints]

sctest(
  roll_var_msft ~ 1,
  type = "Chow",
  point = bp_aapl_3$breakpoints[1],
  data = prices
)

sctest(
  roll_var_msft ~ 1,
  type = "Chow",
  point = bp_aapl_3$breakpoints[2],
  data = prices
)


#Checking for SPY
bp_spy <- breakpoints(
  roll_var_spy ~ 1,
  data = prices
)

summary(bp_spy)

plot(bp_spy)
BIC(bp_spy)
bp_spy_opt <- breakpoints(
  roll_var_spy ~ 1,
  data = prices,
  breaks = 2
)

bp_spy_opt$breakpoints

prices$Date[bp_spy_opt$breakpoints]

sctest(
  roll_var_spy ~ 1,
  type = "Chow",
  point = bp_aapl_3$breakpoints[1],
  data = prices
)

sctest(
  roll_var_spy ~ 1,
  type = "Chow",
  point = bp_aapl_3$breakpoints[2],
  data = prices
)


