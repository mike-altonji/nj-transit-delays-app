"
Functions Code
"
library(plotly)
library(data.table)

filter.df <- function(data, line.in, station.in, date.in) {
  final = data
  if (length(line.in > 0))    {final = subset(final, line %in% line.in)}
  if (length(station.in > 0)) {final = subset(final, station %in% station.in)}
  # need to add date filter next
  
  return(final)
}




create.hist <- function(data, n) {
  reason_counts = data[, .(.N), by = .(block_number)]
  
  phrases = data[, c('block_number', 'reason')]
  setkey(phrases, "block_number")
  phrases = unique(phrases)
  reason_counts = merge(reason_counts, phrases, all.x=T, by='block_number')
  
  # Only show top n reasons
  reason_counts = reason_counts[order(-rank(N))]
  reason_counts = reason_counts[1:n, ]
  
  histogram <- plot_ly(x = reason_counts$reason, y = reason_counts$N, type = "bar")
  return(histogram)
}


create.time <- function(data) {
  keycol <-c("date")
  setorderv(data, keycol)

  # The most recent min value for a line. To be fair.
  maximum = as.Date("2000-01-01")
  for (line.id in unique(data$line)) {
    a = min(subset(data, line == line.id)$date)
    if (a > maximum) {maximum = a}
  }
  data = subset(data, date >= maximum)
  
  data$cum = seq(from=1, to = nrow(data))
  
  time.series <- plot_ly(x = data$date, y = data$cum, type = 'scatter', mode = "lines")
  return(time.series)
}

# create
# 
# 
# reason_counts = reason_counts.reset_index()
# reason_counts['reason'] = reason_counts['index'].apply(lambda x: phrases.get(x))
# reason_counts['reason_str'] = reason_counts['reason'].apply(lambda l: ', '.join(l))
# 
# # reason_counts = reason_counts[reason_counts['count'] >= n]
# reason_counts = reason_counts[:10]