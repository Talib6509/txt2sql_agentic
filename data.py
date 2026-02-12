import json

def get_table_metadata():
    """
    Returns table names and their descriptions in JSON format.
    """

    consolidated_tables = {
    "master_product": {
        "description": "Main table that stores all finished products. Contains basic product information like name, current inventory quantity, selling price, and manufacturing process type. This table serves as the main reference for other systems like quality control and production planning. For every product id corresponding product name, quantity of the product in the stock inventory and price of the product is provided. In Addition to that every product has a process type which is used during manufacturing.",  
        
        "columns": [
            {"name": "product_id", "type": "INT", "description": "Unique identifier code for each product/SKU, primary key"},
            {"name": "product_name", "type": "VARCHAR(50)", "description": "Name of the product"},
            {"name": "stock", "type": "INT", "description": "Quantity of finished product available in inventory, measured in tons"},
            {"name": "price", "type": "INT", "description": "Market price of the product, expressed in USD per unit"},
            {"name": "process_type", "type": "VARCHAR(50)", "description": "Type of manufacturing process applied, determined by the product’s chemical structure, performance requirements, and intended application area"}
        ],
        "relationships": {
                "Foreign Key":"links master_product.product_id to master_product_limits.product_id",
                "Foreign Key":"links master_product.product_id to opt_scenario.product_id"
        },

        "examples": [
            {"product_id":"CH-001", "product_name": "ChemAlloy B12", "stock":4500,"price":12.5, "process_type": "Alloy Blending"},
            {"product_id":"CH-003", "product_name": "PolyNex A7", "stock":3600,"price":9.4, "process_type": "Polymer Compounding"}
        ],
        "usuage": ["How much of this product is present in the stock inventory?",
                   "What is the price of this product?",
                   "What are the various property limits for this product",
                   "Give me the details of optimal scenario for this product"]

    },

    "master_product_limits": {
        "description": "Stores quality control specifications for each product by defining the minimum and maximum acceptable limits for various product properties. This table ensures product consistency and quality standards are maintained by providing the target ranges that must be met during manufacturing. Properties like viscosity, purity, pH, and other quality metrics are defined here for each product ID.",
        "columns": [
            {"name": "id", "type": "INT", "description": "Primary key"},
            {"name": "property", "type": "VARCHAR(100)", "description": "Property name (viscosity, purity, pH, etc.)"},
            {"name": "min_limit", "type": "INT", "description": "Minimum acceptable value"},
            {"name": "max_limit", "type": "INT", "description": "Maximum acceptable value"},
            {"name": "product_id", "type": "INT", "description": "Unique code for each product that the specification belongs to,Foreign key to master_product"}
        ],
        "relationships": {
            "Foreign Key":"links master_product_limits.product_id to master_product.product_id"},
      
        "examples": [
            {"id":"1", "property": "Viscocity (cP)", "min_limit":56.5,"max_limit":58.5, "product_id": "CH-001"},
        {"id":"2", "property": "Purity (%)", "min_limit":26,"max_limit":28, "product_id": "CH-001",}
        ],

        "usuage": ["what are the various property limits for this product?",
                   "Give me the products which has max limit for Viscocity of 52",
                   "Give me the products which has price lower than 15 and Viscocity higher thatn 20"]        
        },

    "master_raw_material": {
        "description": "This table can be used to find information about raw materials used for product recipes. You can link this table to master_raw_material_properties to find the properties of these raw material. You can check the weather information about the stock location from master_location table. You can check the scenerio in which these raw materials are used from opt_recipe table.",
        "columns": [
            {"name": "raw_material_id", "type": "INT", "description": "Unique identifier code for each raw material,Primary key"},
            {"name": "raw_material_name", "type": "VARCHAR(100)", "description": "Name of the raw material"},
            {"name": "unit_cost", "type": "INT", "description": "Purchase cost of the raw material per unit (e.g. per ton), in USD"},
            {"name": "stock_quantity", "type": "INT", "description": "Available inventory (tons)"},
            {"name": "unit_process_cost", "type": "INT", "description": "Processing/handling cost per unit"},
            {"name": "max_recipe_percentage", "type": "INT", "description": "Max allowable percentage in recipe"},
            {"name": "min_recipe_percentage", "type": "INT", "description": "Minimum required percentage in recipe"},
            {"name": "recipe_usage_coefficient", "type": "INT", "description": "Usage multiples required in recipe"},
            {"name": "supplier_name", "type": "VARCHAR(100)", "description": "Primary supplier name"},
            {"name": "stock_location", "type": "INT", "description": "Storage location identifier where the raw material is kept (city name),Foreign key to master_location"},
            {"name": "process_type", "type": "VARCHAR(100)", "description": "Type of  production process"}
        ],
        "relationships": {
            "Foreign Key":"links master_raw_material.stock_location to master_location.location_city",
            "Foreign Key":"links to master_raw_material.raw_material_id to master_raw_material_properties.raw_material_id ",
            "Foreign Key":"links master_raw_material.stock_location to opt_recipe.raw_material_id"
            },
        "examples": [
        {"raw_material_id":"H2", "raw_material_name": "Potassium Carbonate", "unit_cost":89.22,"stock_quantity":1250, "unit_process_cost": 27.1, "max_recipe_percentage":1,"min_recipe_percentage":0,"recipe_usage_coefficient":1,"supplier_name":"NovaChem","stock_location":"İstanbul","process_type":"Dry Mixing"},
        {"raw_material_id":"H1", "raw_material_name": "Sodium Silicate", "unit_cost":48.02,"stock_quantity":1900, "unit_process_cost": 2.62, "max_recipe_percentage":1,"min_recipe_percentage":0,"recipe_usage_coefficient":1,"supplier_name":"ChemSource Ltd.","stock_location":"Ankara","process_type":"Solution Preparation"}
        ],

        "usuage": ["what is the purchase cost of this raw material?",
                   "Which raw materials are sourced by ChemSource Ltd.",
                   "Give me the details of raw materials which are present in SC-01 optimal recipe scenario"] 
    },

    "master_raw_material_properties": {
        "description": "This table provided values for various properties of raw materials. These values can be used in master_raw_material or opt_recipe table information to get a full overview of raw materials.",
        "columns": [
            {"name": "id", "type": "INT", "description": "Primary key"},
            {"name": "property", "type": "VARCHAR(50)", "description": "Measured property name"},
            {"name": "value", "type": "INT", "description": "Measured value"},
            {"name": "raw_material_id", "type": "INT", "description": "Identifier of the raw material to which the property belongs,Foreign key linking to the raw materials table."}
        ],
        "relationships": {
            "Foreign Key":"links master_raw_material_properties.raw_material_id to master_raw_material.raw_material_id",
            "Foreign Key":"links master_raw_material_properties.raw_material_id to opt_recipe.raw_material_id",

        },
        "examples": [
            {"id":"1", "property": "Viscocity (cP)", "value":56.5,"raw_material_id":'H1'},
            {"id":"1", "property": "Purity (%)", "value":30.08,"raw_material_id":'H1'}

        ],
        
        "usuage": ["what are the properties of this raw material?",
                   "Give me the Viscocity of raw materials which are present in SC-01 optimal recipe scenario",
                   "What the number of stock inventory for raw materials where Viscocity is less than 40"]    
        },


    "opt_scenario": {
        "description":"This Table gives various scenarios for product manufacturing. Each scenario is classified as Optimal or not and is approved by the user and holds information like  target_recipe_amount, total_process_cost etc. We can join more product information form master_product table and to get more information about the scenarios we can join opt_recipe_properties and opt_recipe tables. For every scenario id which raw material is used and how much of it is used in each optimal scenario.",
        "columns": [
            {"name": "scenario_id", "type": "INT", "description": "Primary key"},
            {"name": "status", "type": "VARCHAR(100)", "description": "Optimal / Infeasible"},
            {"name": "user_approval", "type": "INT", "description": "Indicator showing whether the user has reviewed/approved the scenario (1 = approved, 0 = not approved)"},
            {"name": "what_if_from", "type": "VARCHAR(100)", "description": "Reference scenario for what-if analysis"},
            {"name": "target_recipe_amount", "type": "INT", "description": "Total desired production quantity"},
            {"name": "total_cost", "type": "INT", "description": "Total scenario cost"},
            {"name": "total_raw_material_cost", "type": "INT", "description": "Raw material cost"},
            {"name": "total_process_cost", "type": "INT", "description": "Processing cost"},
            {"name": "number_of_raw_materials_used", "type": "INT", "description": "The number of distinct raw materials included in the optimal recipe"},
            {"name": "product_id", "type": "INT", "description": "Product code for which the recipe optimization scenario was generated. Foreign key to master_product"}
        ],
        "relationships": {
        "Foreign Key":"links opt_scenario.product_id to master_product.product_id",
        "Foreign Key":"links opt_scenario.scenario_id to opt_recipe.scenario_id",
        "Foreign Key":"links opt_scenario.scenario_id to opt_recipe_properties.scenario_id",

        },
        "examples": [
        {"scenario_id":"SC-1", "status": "Optimal", "user_approval":0,"what_if_from":None, "target_recipe_amount": 400,"total_cost":21355.97, "total_raw_material_cost": 19226.84, "total_process_cost":2129.13,"number_of_raw_materials_used":6, "product_id": "CH-001"},
        {"scenario_id":"SC-2", "status": "Optimal", "user_approval":1,"what_if_from":'SC-1', "target_recipe_amount": 400,"total_cost":21357.35, "total_raw_material_cost": 19228.74, "total_process_cost":2128.61,"number_of_raw_materials_used":5, "product_id": "CH-002"}
        ],
        
        "usuage": ["For scenario id 123 what are the raw materials used",
                   "Give me the scenario where all products have maxium Purity limit of 28"] 
    },

    "opt_recipe": {
        "description": "This Table gives information about how much raw material is used in different scenarios. Also what is the percentage of that raw material in the full recipe. Raw Materials can have different quantity for different scenarios",
        "columns": [
            {"name": "record_id", "type": "INT", "description": "Primary key"},
            {"name": "recipe_quantity", "type": "INT", "description": "Raw material quantity in tons"},
            {"name": "recipe_percentage", "type": "INT", "description": "Percentage share of the raw material within the total recipe amount"},
            {"name": "raw_material_id", "type": "INT", "description": "Identifier of the raw material used in the optimized recipe. Foreign key to master_raw_material"},
            {"name": "scenario_id", "type": "INT", "description": "Identifier of the optimization scenario to which this recipe composition belongs. Foreign key to opt_scenario"}
        ],
        "relationships": {
            
            "Foreign Key":"links opt_recipe.raw_material_id to master_raw_material.raw_material_id",
            "Foreign Key":"links opt_recipe.scenario_id to opt_scenario.scenario_id",
            },
        "examples": [
            {"record_id":"1", "recipe_quantity": 1, "recipe_percentage":0,"raw_material_id":'H1',"scenario_id":"SC-1"},
            {"record_id":"3", "recipe_quantity": 300, "recipe_percentage":0.13,"raw_material_id":'H1',"scenario_id":"SC-2"},

        ],
        "usuage":["What is the recipe quantity for this material in SC-1 scenario",
                  "What is the total quantity for this material across all scenarios",
                  "Which raw material is short in the inventory for all scenarios combined"]
    },


    "opt_recipe_properties": {
        "description": "This table gives information about whether the different property values of a particular scenario are lying within the min and max limits.",
        "columns": [
            {"name": "record_id", "type": "INT", "description": "Primary key"},
            {"name": "property", "type": "VARCHAR(100)", "description": "Evaluated property"},
            {"name": "value", "type": "INT", "description": "Computed value"},
            {"name": "min_limit", "type": "INT", "description": "Min allowed value"},
            {"name": "max_limit", "type": "INT", "description": "Max allowed value"},
            {"name": "scenario_id", "type": "INT", "description": "Identifier of the optimization scenario for which the property values were computed. Foreign key to opt_scenario"}
        ],
        "relationships": {  
        "Foreign Key":"links opt_recipe_properties.scenario_id to opt_scenario.scenario_id",
        },

        "examples": [
        {"record_id":"1", "property": "Viscocity (cP)", "value":56.52,"min_limit":56.5,"max_limit":58.5,"scenario_id":"SC-1"},
        {"record_id":"4", "property": "Purity (%)", "value":26.04,"min_limit":26,"max_limit":28,"scenario_id":"SC-2"}
        ],
        
        "usuage": ["Which scenario is having the highest purity",
                   "Give me the scenario where the max limit for Density is 28"] 
        },

    "master_location": {
        "description": "Stores master data for plant/city locations, including coordinates and weather constraints.",
        "columns": [
            {"name": "location_id", "type": "INT", "description": "Primary key"},
            {"name": "location_city", "type": "VARCHAR(100)", "description": "City name"},
            {"name": "location_latitude", "type": "INT", "description": "Latitude"},
            {"name": "location_longitude", "type": "INT", "description": "Longitude"},
            {"name": "weather_lower_limit", "type": "INT", "description": "Min allowed temperature"},
            {"name": "weather_upper_limit", "type": "INT", "description": "Max allowed temperature"}
        ],
        "relationships": {
            "Foreign Key":"links master_location.location_city to master_raw_material.stock_location",
        },
        "examples": [
        {"location_id":"1", "location_city": "İstanbul", "location_latitude":32.52,"location_longitude":35.33,"weather_lower_limit":8,"weather_upper_limit":22},
        {"location_id":"3", "location_city": "Bursa", "location_latitude":29.52,"location_longitude":56.5,"weather_lower_limit":10,"weather_upper_limit":25},
        ],

        "usuage": ["Which city is having a higher weather limit?"] 
                       
        }
}

    return json.dumps(consolidated_tables, indent=4)


