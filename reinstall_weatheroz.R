# Remove and reinstall weatherOz from CRAN
# This script will force remove the current weatherOz and install the CRAN version

cat("Detaching weatherOz if loaded...\n")
# First try to detach the package if it's loaded
tryCatch({
  detach("package:weatherOz", unload = TRUE)
  cat("weatherOz detached successfully.\n")
}, error = function(e) {
  cat("weatherOz was not loaded or could not be detached.\n")
})

cat("Force removing current weatherOz package...\n")
# Check if weatherOz is installed and force remove it
if ("weatherOz" %in% rownames(installed.packages())) {
  # Force remove even if in use
  tryCatch({
    remove.packages("weatherOz")
    cat("weatherOz removed successfully.\n")
  }, error = function(e) {
    cat("Error removing weatherOz:", e$message, "\n")
    cat("Attempting to force remove...\n")
    # Try to force remove from library path
    lib_path <- .libPaths()[1]
    weatheroz_path <- file.path(lib_path, "weatherOz")
    if (dir.exists(weatheroz_path)) {
      unlink(weatheroz_path, recursive = TRUE, force = TRUE)
      cat("Forced removal of weatherOz directory.\n")
    }
  })
} else {
  cat("weatherOz was not installed.\n")
}

cat("Installing weatherOz from CRAN...\n")
# Install weatherOz from CRAN with dependencies
install.packages("weatherOz", repos = "https://cran.r-project.org", dependencies = TRUE, force = TRUE)

cat("Verifying installation...\n")
# Test if weatherOz loads correctly
tryCatch({
  library(weatherOz)
  cat("SUCCESS: weatherOz loaded successfully!\n")
  
  # Show package info
  cat("Package version:", as.character(packageVersion("weatherOz")), "\n")
  
}, error = function(e) {
  cat("ERROR loading weatherOz:", e$message, "\n")
})

cat("Package management complete.\n")
