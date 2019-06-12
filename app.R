library(data.table)
library(reticulate)
library(shiny)
library(DT)

setwd('C:/Users/mikea/Documents/Analytics/NJ Transit/nj_transit/')
source('C:/Users/mikea/Documents/Analytics/NJ Transit/nj_transit/funcs.R')

### Returns "data" and "phrases"
source_python('C:/Users/mikea/Documents/Analytics/NJ Transit/nj_transit/summarize_tweets.py')
setDT(data)
data$date = as.Date(data$time) # date doesn't transfer correctly from Python

                     
" App Starts Here "
ui <- fluidPage(
  titlePanel("NJ Transit Delays"),
  sidebarLayout(
    sidebarPanel(
      
      # Inputs -------------
      selectizeInput("line", "Line", choices = unique(data$line), multiple=T), 
      selectizeInput("station", "Station", choices = unique(data$station), multiple=T), 
      dateRangeInput("date", "Date", min = min(data$date), max = max(data$date), start = min(data$date), end = max(data$date)), 
      # still need time of day filter
      # Need to add delay/cancelation view
      numericInput("n", "Number of Reasons", min=1, max=100, value=10)
    ), # End Sidebarpanel
    
    # Main panel -----------
    mainPanel(
      # DTOutput("table"), 
      plotlyOutput('histogram')
    )
  )
)

" Server Code "
server <- function(input, output) {
  
  data.filter = reactive(filter.df(data, input$line, input$station, input$date))
  output$table <- renderDT({data.filter()})
  histogram = reactive(create.hist(data.filter(), input$n))
  output$histogram <- renderPlotly({histogram() })
  
}

shinyApp(ui = ui, server = server)


