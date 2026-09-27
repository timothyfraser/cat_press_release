# fig/src/chart_tompkins_2020_print.R
# Print-size redraw of the REPORTER's vehicle-type chart for Figure 1.
#
# The REPORTER draws this chart in the browser at 1920 x 1200 px (1.6:1) for a
# Word page, which leaves its labels tiny at journal size. For the figure we
# redraw it with ggplot2 (the REPORTER's own server-side chart engine) from the
# exact values in the generated release (fig/src/press_release_tompkins_2020.docx)
# and the same colours, near-square so it sits beside the three bullets.
#
#   Rscript fig/src/chart_tompkins_2020_print.R   ->  fig/src/chart_tompkins_2020_print.png

library(ggplot2)
library(dplyr)

shares = tibble(
  type  = c("Light Truck", "Car/Bike", "Heavy Truck", "Combo Truck", "Bus"),
  share = c(48.8, 27.7, 11.0, 10.7, 1.9),          # from the generated release
  fill  = c("#648fff", "#ffb000", "#fe6100", "#785ef0", "#dc267f")   # sampled from its chart
) |>
  mutate(type = factor(type, levels = type),
         label = sprintf("%.1f%%", share))

p = ggplot(shares, aes(x = type, y = share, fill = type)) +
  geom_col(width = 0.72) +
  geom_text(aes(label = label), vjust = -0.45, size = 5.6, fontface = "bold", colour = "#1b1b1b") +
  scale_fill_manual(values = setNames(shares$fill, shares$type), guide = "none") +
  scale_x_discrete(labels = function(x) sub(" ", "\n", x)) +
  scale_y_continuous(labels = function(v) paste0(v, "%"), limits = c(0, 55),
                     breaks = seq(0, 50, 10), expand = expansion(mult = c(0, 0.02))) +
  labs(title = expression(bold(CO[2]~"Equivalent Emissions by Vehicle Type")),
       subtitle = "Tompkins County, NY, 2020",
       x = NULL, y = "Share of emissions (%)") +
  theme_minimal(base_size = 17) +
  theme(plot.title = element_text(size = 17, margin = margin(b = 2)),
        plot.subtitle = element_text(size = 14, colour = "#555555", margin = margin(b = 8)),
        plot.title.position = "plot",
        axis.title.y = element_text(size = 15, margin = margin(r = 4)),
        axis.text.y = element_text(size = 14, colour = "#333333"),
        axis.text.x = element_text(size = 14, colour = "#222222", lineheight = 0.9),
        panel.grid.major.x = element_blank(),
        panel.grid.minor = element_blank(),
        panel.grid.major.y = element_line(colour = "#e3e3e3"),
        axis.line.x = element_line(colour = "#777777"),
        plot.margin = margin(6, 8, 4, 4))

out = file.path("fig", "src", "chart_tompkins_2020_print.png")
ggsave(out, p, width = 5.2, height = 5.4, dpi = 300, bg = "white", device = ragg::agg_png)
message("wrote ", out)
