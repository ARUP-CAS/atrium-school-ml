library(tidyverse)

sh <- googlesheets4::read_sheet("https://docs.google.com/spreadsheets/d/1lA7_fdx4ZHQbcGGCsgA1sQFfUSBjEUsJIIzpW5FU2Uo/edit?pli=1&gid=164942495#gid=164942495", sheet = "attending") %>% 
  mutate(
       p = str_extract(name, ".+(?=,)"),
       p = stringi::stri_trans_general(str_to_lower(p), "Latin-ASCII"),
       p = str_replace_all(p, "\\s", "-")) %>% 
  select(p, name, country)

fl <- list.files(here::here("reports/"), pattern = "\\.pdf") %>% 
  as_tibble() %>% 
#   filter(!str_detect(value, "comments")) %>% 
  mutate(p = str_extract(value, ".+(?=\\.pdf$)"),
         p = str_to_lower(p))

full_join(sh, fl, by = join_by("p")) %>% 
  mutate(path = if_else(!is.na(value), paste0("reports/", value), NA),
         Report = if_else(!is.na(value), paste0("[Report (PDF)](", path, ")"), "*To be submitted.*")) %>% 
  select(Name = name, Country = country, Report) %>% 
  arrange(Name) |> 
  write_csv(here::here("reports/list.csv"))
  
