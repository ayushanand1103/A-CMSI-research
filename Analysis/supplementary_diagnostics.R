# Run from the repository root after python run_acmsi.py.
# Exact R strucchange break estimates and rugarch diagnostics are descriptive.
root <- normalizePath(Sys.getenv("ACMSI_ROOT", unset = getwd()), winslash = "/")
out <- file.path(root, "outputs", "tables")
dir.create(out, recursive = TRUE, showWarnings = FALSE)
suppressPackageStartupMessages({library(strucchange); library(rugarch); library(zoo)})
prices <- read.csv(file.path(root, "Data", "prices_clean.csv"))
prices$Date <- as.Date(prices$Date, format = "%d-%m-%Y")
stopifnot(!anyNA(prices$Date), !anyDuplicated(prices$Date))
residuals <- read.csv(file.path(root, "Data", "arima_residuals.csv"))
break_rows <- list()
for (asset in c("AAPL", "MSFT", "SPY")) {
  ret <- diff(log(prices[[asset]]))
  variance <- rollapply(ret, 21, var, align = "right", fill = NA)
  keep <- !is.na(variance)
  data <- data.frame(Date = prices$Date[-1][keep], variance = variance[keep])
  fit <- breakpoints(variance ~ 1, data = data, h = 252, breaks = 5)
  chosen <- breakpoints(fit)
  indices <- chosen$breakpoints
  if (!all(is.na(indices))) for (b in indices[!is.na(indices)]) {
    test <- sctest(variance ~ 1, type = "Chow", point = b, data = data)
    break_rows[[length(break_rows)+1]] <- data.frame(asset = asset, date = data$Date[b],
      chow_f = unname(test$statistic), chow_p_naive = test$p.value,
      interpretation = "offline_selected_break_naive_p_descriptive")
  }
  sink(file.path(out, paste0("R_Bai_Perron_", asset, ".txt")))
  print(summary(fit)); print(summary(chosen))
  if (!all(is.na(indices))) tryCatch(print(confint(fit)),
    error = function(e) cat("Confidence interval unavailable:", conditionMessage(e), "\n"))
  sink()
  # Existing full-sample ARIMA innovations: supplemental descriptive diagnostics.
  x <- residuals[[paste0(asset, "_RESID")]]
  sink(file.path(out, paste0("R_GARCH_diagnostics_", asset, ".txt")))
  for (kind in c("sGARCH", "eGARCH", "gjrGARCH")) for (distribution in c("norm", "std")) {
    spec <- ugarchspec(variance.model = list(model = kind, garchOrder = c(1, 1)),
      mean.model = list(armaOrder = c(0, 0), include.mean = FALSE), distribution.model = distribution)
    fitted <- ugarchfit(spec, x, solver = "hybrid")
    cat("\nMODEL", asset, kind, distribution, "\n")
    show(fitted)
    if (fitted@fit$convergence == 0) {
      print(infocriteria(fitted)); print(nyblom(fitted)); print(signbias(fitted))
    }
  }
  sink()
}
if (length(break_rows)) write.csv(do.call(rbind, break_rows),
  file.path(out, "R_Bai_Perron_Chow.csv"), row.names = FALSE)
