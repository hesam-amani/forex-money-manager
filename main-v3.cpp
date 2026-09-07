#include <iostream>
#include <iomanip>
#include <vector>
#include <unordered_set>

void printHeader() {
    std::cout << "\n                                                                                                   ";
    std::cout << "\n   _____                    _____                    _____                                   _     ";
    std::cout << "\n  |   __|___ ___ ___ _ _   |     |___ ___ ___ _ _   |     |___ ___ ___ ___ ___ _____ ___ ___| |_   ";
    std::cout << "\n  |   __| . |  _| -_|_'_|  | | | | . |   | -_| | |  | | | | .'|   | .'| . | -_|     | -_|   |  _|  ";
    std::cout << "\n  |__|  |___|_| |___|_,_|  |_|_|_|___|_|_|___|_  |  |_|_|_|__,|_|_|__,|_  |___|_|_|_|___|_|_|_|    ";
    std::cout << "\n                                             |___|                    |___|                        ";
    std::cout << "\n                                                                                                   ";
    std::cout << "\n                          _____                   _ _ _     _ ___ ___ ___                          ";
    std::cout << "\n                         |     |_____ ___ ___ ___| | | |___| |  _|_  |_  |                         ";
    std::cout << "\n                         |  |  |     | -_| . | .'| | | | . | |  _|_  | | |                         ";
    std::cout << "\n                         |_____|_|_|_|___|_  |__,|_____|___|_|_| |___| |_|                         ";
    std::cout << "\n                                         |___|                                                     ";
    std::cout << "\n                                                                                                   ";
}

void printTable(const std::vector<std::vector<float>>& table, const std::vector<std::string>& columnTitles, int rowCount) {
    if (table.empty()) return;  // Prevents printing an empty table

    const int columnWidth = 15;
    const int numColumns = columnTitles.size();

    std::string horizontalBorder = "+";

    for (int i = 0; i < numColumns; i++) {
        horizontalBorder += std::string(columnWidth + 2, '-') + "+";
    }

    std::cout << horizontalBorder << "\n|";

    for (const auto& title : columnTitles) {
        std::cout << " " << std::setw(columnWidth) << std::left << title << " |";
    }

    std::cout << "\n" << horizontalBorder << "\n";

    for (int i = 0; i < rowCount; i++) {  // Ensures correct row count is printed
        std::cout << "|";
        for (const auto& value : table[i]) {
            std::cout << " " << std::setw(columnWidth) << std::left << value << " |";
        }
        std::cout << "\n";
    }

    std::cout << horizontalBorder << "\n";
}

int main() {
    const int m = 7;  // Number of columns

    // Print header
    printHeader();

    // Static column titles
    std::vector<std::string> columnTitles = {
        "Balance", "Risk", "Risk of Money", "Protective Stop", "Pip Value", "Trade Volume", "Pip per Lot"
    };

    // Excluding columns from input
    std::unordered_set<int> excludeColumns = {2, 4, 5};

    std::vector<std::vector<float>> table;  // Stores all generated rows

    int rowNumber = 1;  // Keeps track of how many rows are generated

    while (true) {  // Infinite loop to keep generating rows
        std::vector<float> row(m);

        std::cout << "\n\nEnter values for row " << rowNumber << "\n-------------------------" << std::endl;

        for (int j = 0; j < m; ++j) {
            if (excludeColumns.find(j) != excludeColumns.end()) {
                continue;  // Skip input for calculated columns
            }

            std::cout << columnTitles[j] << ": ";
            std::cin >> row[j];

            if (std::cin.fail()) {  // Stop if input is invalid (Ctrl+D / Ctrl+Z)
                std::cout << "\n\nStopping table generation. Press Enter to exit...\n";
                std::cin.get();
                return 0;
            }
        }

        // Calculate excluded columns
        row[2] = row[0] * row[1] / 100;  // Risk of Money
        row[4] = row[2] / row[3];        // Pip Value
        row[5] = row[4] / row[6];        // Trade Value

        table.push_back(row);  // Add new row to the table

        // Print the current table
        std::cout << "-------------------------\n\nCurrent table after row " << rowNumber << "\n";

        printTable(table, columnTitles, table.size());

        rowNumber++;  // Increase row counter
    }

    return 0;
}
