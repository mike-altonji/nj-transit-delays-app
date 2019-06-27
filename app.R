library(data.table)
library(shiny)
library(shinyTime)
library(DT)

setwd('C:/Users/mikea/Documents/Analytics/NJ Transit/nj_transit/')
source('C:/Users/mikea/Documents/Analytics/NJ Transit/nj_transit/funcs.R')

### Returns "data" and "phrases"
# source_python('C:/Users/mikea/Documents/Analytics/NJ Transit/nj_transit/data_for_R.py')
data = read.csv('C:/Users/mikea/Documents/Analytics/NJ Transit/data.csv')
data$date = as.Date(data$date, format = "%Y-%m-%d") # date doesn't transfer correctly from Python
data$time_train = as.ITime(strptime(data$time_train, "%l:%M%p")) # Will set date portion to today, but shouldn't matter. I just want time.
data$reason = as.character(data$reason)
setDT(data)

# Find the furthest point in the past for each train-line, then grab the newest of all of those. That's as far back as we'll look.
min.even.date = as.Date("2000-01-01")
for (line.id in unique(data$line)) {
  a = min(subset(data, line == line.id)$date)
  if (a > min.even.date) {min.even.date = a}
}

" App Starts Here "
ui <- fluidPage(
  titlePanel("NJ Transit Delays"),
  sidebarLayout(
    sidebarPanel(
      
      # Inputs -------------
      checkboxGroupInput("type", "Delays, Cancelations, or Both?", choices = c("Delays" = 'delay', "Cancelations" = 'cancel'), 
                         inline=T, selected=c('delay', 'cancel')), 
      br(), 
      selectizeInput("line", "Line", choices = unique(data$line), multiple=T), 
      selectizeInput("station", "Station", choices = unique(data$station), multiple=T), 
      dateRangeInput("date", "Date", min = min(data$date), max = max(data$date), start = min.even.date, end = max(data$date)), 
      fluidRow(column(12, h4('Station Departure Time Filter')), align='center'), 
      fluidRow(column(6, timeInput("time.start", "Start Time Range", seconds = FALSE)), # still need time of day FILTER.
               column(6, timeInput("time.end", "End Time Range", seconds = FALSE, value = strptime("23:59:59", "%T"))), align = 'center' ), 

      br(), 
      numericInput("n", "Number of Reasons", min=1, max=100, value=10)
    ), # End Sidebarpanel
    
    # Main panel -----------
    mainPanel(
      # DTOutput("table"), 
      plotlyOutput('histogram'), 
      br(), br(), 
      plotlyOutput('time.series')
    )
  )
)

" Server Code "
server <- function(input, output) {
  
  data.filter = reactive(filter.df(data, input$line, input$station, input$date, input$time.start, input$time.end, input$type))
  output$table <- renderDT({data.filter()})
  histogram = reactive(create.hist(data.filter(), input$n))
  output$histogram <- renderPlotly({histogram() })
  time.series = reactive(create.time(data.filter() ))
  output$time.series <- renderPlotly({time.series() })
  
}

shinyApp(ui = ui, server = server)


