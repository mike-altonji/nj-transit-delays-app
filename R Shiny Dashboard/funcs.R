"
Functions Code
"
library(plotly)
library(data.table)

filter.df <- function(data, line.in, station.in, date.in, time.start, time.end, types) {
  final = data
  if (length(line.in > 0))    {final = subset(final, line %in% line.in)}
  if (length(station.in > 0)) {final = subset(final, station %in% station.in)}
  if (time.end > time.start) {
    final = subset(final, time_train >= as.ITime(time.start))
    final = subset(final, time_train <= as.ITime(time.end))
  }
  final = subset(final, date >= date.in[1] & date <= date.in[2])
  
  # Picking Delays or Cancelations
  if (!('cancel' %in% types)) {final = subset(final, Cancel == "False")}
  if (!('delay' %in% types))  {final = subset(final,  Delay == "False")}
  
  # The most recent minimum date of all selected train-lines. To give an even starting point.
  maximum = as.Date("2000-01-01")
  for (line.id in unique(final$line)) {
    a = min(subset(final, line == line.id)$date)
    if (a > maximum) {maximum = a}
  }
  final = subset(final, date >= maximum)
  
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
  
  histogram <- plot_ly(source = 'hover_bar', x = reason_counts$reason, y = reason_counts$N, type = "bar") %>% 
    layout(title = "Most Common Reasons for Delays")
  
  
  return(histogram)
}


create.time <- function(data) {
  
  # Subset data that's been hovered over
  hover_data  <- event_data("plotly_hover", source = "hover_bar")
  select_data <- event_data("plotly_click", source = "hover_bar")
  
  
  ### ISSUE!!! # on bar graph > # cumulatively displayed...why??? block number issue??? idk!!!
  phrases = data[, c('block_number', 'reason')]
  setkey(phrases, "block_number")
  phrases = unique(phrases)
  
  block.hover = subset(phrases, reason %in%  hover_data$x)$block_number[1]
  block.click = subset(phrases, reason %in% select_data$x)$block_number[1]
  
  if (!is.null(hover_data) & !(is.null(select_data))) {
    data = subset(data, block_number == block.hover | block_number == block.click)
  } else if (!is.null(hover_data)) {
    data = subset(data, block_number == block.hover)
  } else if (!is.null(select_data)) {
    data = subset(data, block_number == block.click)}
  
  keycol <-c("date")
  setorderv(data, keycol)

  data$cum = seq(from=1, to = nrow(data))
  
  time.series <- plot_ly(x = data$date, y = data$cum, type = 'scatter', mode = "lines") %>% 
    layout(title = "Delay Trends Over Time")
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