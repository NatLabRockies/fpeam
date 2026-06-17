# production table identifier (feedstock_measure in production data)
feedstock_measure_type = string(default='harvested')

# emission factors as lb pollutant per lb resource subtype
emission_factors = filepath(default='data/inputs/emission_factors.csv')

# resource subtype distribution for all resources
resource_distribution = filepath(default='data/inputs/resource_distribution.csv')

# --- dynamic provider options (all optional) ---

# Provider name or dotted Python import path.
# Built-in values: "table" (default), "ammonia_fertilizer"
# Example: provider = "ammonia_fertilizer"
provider = string(default='table')

# Path to geophysical context CSV (required when provider != 'table')
# Columns: region, and any subset of temperature_c, wind_speed_m_s,
#          precipitation_mm, soil_type, year, month.
geophysical_context = string(default='')

# Path to provider-specific parameter CSV.
# Defaults to the bundled ammonia_provider_params.csv when using
# the ammonia_fertilizer provider.
provider_params = string(default='')
