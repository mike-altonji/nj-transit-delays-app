"
Functions Code for NJ Transit Delays Dashboard
"

# Import libraries
library(plotly)
library(data.table)


filter.df <- function(data, line.in, station.in, date.in, time.start, time.end, types) {
  "
  Filters the dataset down based on the user-selected filters
  "
  final = data
  
  # Filters on line, station, and time of delay
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
  
  # Picks the most recent minimum date of all selected train-lines. To give an even starting point.
  maximum = as.Date("2000-01-01")
  for (line.id in unique(final$line)) {
    a = min(subset(final, line == line.id)$date)
    if (a > maximum) {maximum = a}
  }
  final = subset(final, date >= maximum)
  
  return(final)
}


create.barplot <- function(data, n) {
  "
  Creates a bar graph of the 'n' most common delay reasons
  "

  reason_counts = data[, .(.N), by = .(block_number)]
  phrases = data[, c('block_number', 'reason')]
  setkey(phrases, "block_number")
  phrases = unique(phrases)
  reason_counts = merge(reason_counts, phrases, all.x=T, by='block_number')
  
  # Only show top n reasons
  reason_counts = reason_counts[order(-rank(N))]
  reason_counts = reason_counts[1:n, ]
  
  barplot <- plot_ly(source = 'hover_bar', x = reason_counts$reason, y = reason_counts$N, type = "bar") %>% 
    layout(title = "Most Common Reasons for Delays")
  
  return(barplot)
}


create.time <- function(data) {
  "
  Creates a line graph showing the cumulation of delays
  "
  
  # Subset data that's been hovered over
  hover_data  <- event_data("plotly_hover", source = "hover_bar")
  select_data <- event_data("plotly_click", source = "hover_bar")
  
  # TODO: Issue...Number on bar graph is greater than the cumulatively displayed number. Could be a block_number issue.
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
