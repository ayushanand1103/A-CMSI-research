library(zoo)
library(dplyr)

vol_data <- read.csv("C:/A-CMSI research/Data/GARCH vol/Merged_Volatility.csv")

vol_data$Date <- as.Date(vol_data$Date, format = "%d-%m-%Y")

# AAPL
aapl_mean <- rollapply(
  vol_data$AAPL_vol,
  width = 252,
  FUN = mean,
  fill = NA,
  align = "right"
)

aapl_sd <- rollapply(
  vol_data$AAPL_vol,
  width = 252,
  FUN = sd,
  fill = NA,
  align = "right"
)

vol_data$AAPL_V <- (vol_data$AAPL_vol - aapl_mean) / aapl_sd

#MSFT
msft_mean <- rollapply(
  vol_data$MSFT_vol,
  width = 252,
  FUN = mean,
  fill = NA,
  align = "right"
)

msft_sd <- rollapply(
  vol_data$MSFT_vol,
  width = 252,
  FUN = sd,
  fill = NA,
  align = "right"
)

vol_data$MSFT_V <- (vol_data$MSFT_vol - msft_mean) / msft_sd

#SPY
spy_mean <- rollapply(
  vol_data$SPY_vol,
  width = 252,
  FUN = mean,
  fill = NA,
  align = "right"
)

spy_sd <- rollapply(
  vol_data$SPY_vol,
  width = 252,
  FUN = sd,
  fill = NA,
  align = "right"
)

vol_data$SPY_V <- (vol_data$SPY_vol - spy_mean) / spy_sd

vol_data$AAPL_V <- pmax(pmin(vol_data$AAPL_V, 3), -3)
vol_data$MSFT_V <- pmax(pmin(vol_data$MSFT_V, 3), -3)
vol_data$SPY_V  <- pmax(pmin(vol_data$SPY_V, 3), -3)

vt_data <- na.omit(
  vol_data[, c(
    "Date",
    "AAPL_V",
    "MSFT_V",
    "SPY_V"
  )]
)

dim(vt_data)
head(vt_data)

write.csv(
  vt_data,
  "C:/A-CMSI research/Data/V_component.csv",
  row.names = FALSE
)

plot(
  vt_data$Date,
  vt_data$SPY_V,
  type = "l",
  main = "SPY V(t)",
  xlab = "Date",
  ylab = "Normalized Volatility"
)

abline(h = c(-1, 0, 1), lty = 2)


summary(vt_data$SPY_V)

table(vt_data$SPY_V == 3)
table(vt_data$SPY_V == -3)

par(mfrow=c(3,1))

plot(vt_data$Date, vt_data$AAPL_V,
     type="l", main="AAPL V(t)")

plot(vt_data$Date, vt_data$MSFT_V,
     type="l", main="MSFT V(t)")

plot(vt_data$Date, vt_data$SPY_V,
     type="l", main="SPY V(t)")
summary(vt_data[, c("AAPL_V","MSFT_V","SPY_V")])
cor(vt_data[, c("AAPL_V","MSFT_V","SPY_V")])
