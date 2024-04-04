import subprocess

try:
    # Run pytest command and capture the output
    output = subprocess.check_output(
        ["pytest-3", "--tb=line", "-rF", "pytesting/test_caffeine_monitor.py"],
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
except subprocess.CalledProcessError as e:
    # If pytest returns a non-zero exit status, capture the output from the exception
    output = e.output

# Split the output into lines
lines = output.split("\n")

# Initialize variables
collected_line = ""
failed_tests = []

# Process each line
for line in lines:
    if line.startswith("collected"):
        collected_line = line.split(" ")[0]  # Extract only the number of collected items
    elif line.startswith("FAILED"):
        test_name = line.split("::")[1]  # Extract the test name
        test_name = test_name.split("[")[0]  # Remove any parametrized test details
        test_name = test_name.split(" ")[0]  # Remove any error messages
        if test_name not in failed_tests:
            failed_tests.append(test_name)

# Print the desired output
print(collected_line)
for test_name in failed_tests:
    print(f"FAILED {test_name}")
