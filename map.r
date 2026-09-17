library(tidyverse)
library(sf)

sh <- googlesheets4::read_sheet("https://docs.google.com/spreadsheets/d/1lA7_fdx4ZHQbcGGCsgA1sQFfUSBjEUsJIIzpW5FU2Uo/edit?gid=164942495#gid=164942495", sheet = "attending")

co <- giscoR::gisco_countries_2024

sh[!sh$country %in% co$NAME_ENGL, ]
colnames(sh)

origins <- sh %>%
  group_by(country) %>% 
  count() %>% 
  mutate(n = as.character(n)) %>% 
  left_join(co, by = join_by(country == NAME_ENGL)) %>% 
  st_as_sf()

ggplot() +
  geom_sf(data = co) +
  geom_sf(data = origins, aes(fill = n)) +
  coord_sf(xlim = c(-10, 40), ylim = c(30, 65)) +
  scale_fill_brewer(palette = "YlGnBu") +
  theme_minimal() +
  guides(fill = guide_legend(position = "inside", title = "")) +
  theme(legend.position.inside = c(0.9, 0.9), 
        plot.background = element_rect(fill = "white", color = NA))

ggsave(here::here("figs/map.png"), width = 8, height = 7.3)  

# sh$name |> length()
