import SwiftUI

/// 3-step new shelf creation flow: Name → Dimensions → Photo
struct NewShelfView: View {
    let onCreated: (Shelf) -> Void
    @Environment(\.dismiss) private var dismiss
    @State private var step = 0
    @State private var shelfName = ""
    @State private var rowCount = 4
    @State private var columnCount = 6

    var body: some View {
        NavigationStack {
            VStack {
                // Step indicator
                HStack(spacing: 8) {
                    ForEach(0..<2, id: \.self) { i in
                        Circle()
                            .fill(i <= step ? Color.brown : Color(.systemGray4))
                            .frame(width: 8, height: 8)
                    }
                }
                .padding(.top)

                switch step {
                case 0:
                    nameStep
                case 1:
                    dimensionsStep
                default:
                    EmptyView()
                }
            }
            .navigationTitle(step == 0 ? "Name Your Shelf" : "Shelf Size")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    if step > 0 {
                        Button("Back") { step -= 1 }
                    } else {
                        Button("Cancel") { dismiss() }
                    }
                }
            }
        }
    }

    private var nameStep: some View {
        VStack(spacing: 24) {
            Text("Give your shelf a name")
                .font(.headline)

            TextField("e.g., Living Room Left", text: $shelfName)
                .textFieldStyle(.roundedBorder)
                .padding(.horizontal, 32)

            // Quick name suggestions
            VStack(spacing: 8) {
                ForEach(["Living Room", "Study", "Bedroom", "Office"], id: \.self) { name in
                    Button(action: { shelfName = name }) {
                        HStack {
                            Text(name)
                                .foregroundColor(.primary)
                            Spacer()
                            if shelfName == name {
                                Image(systemName: "checkmark")
                                    .foregroundColor(.brown)
                            }
                        }
                        .padding(.horizontal, 16)
                        .padding(.vertical, 10)
                        .background(Color(.systemGray6))
                        .clipShape(RoundedRectangle(cornerRadius: 8))
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(.horizontal, 32)

            Spacer()

            Button(action: { step = 1 }) {
                Text("Continue")
                    .font(.headline)
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(Color.brown)
                    .clipShape(RoundedRectangle(cornerRadius: 14))
            }
            .padding(.horizontal, 32)
            .padding(.bottom, 48)
        }
    }

    private var dimensionsStep: some View {
        VStack(spacing: 24) {
            Text("How many shelves and books per row?")
                .font(.headline)

            VStack(spacing: 20) {
                Stepper("Rows: \(rowCount)", value: $rowCount, in: 1...10)
                Stepper("Columns: \(columnCount)", value: $columnCount, in: 1...20)
            }
            .padding(.horizontal, 32)

            Text("Count the shelves and estimate books per row. You can adjust later.")
                .font(.caption)
                .foregroundColor(.secondary)

            Spacer()

            Button(action: { createShelf() }) {
                Label("Take Photo", systemImage: "camera.fill")
                    .font(.headline)
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(Color.brown)
                    .clipShape(RoundedRectangle(cornerRadius: 14))
            }
            .padding(.horizontal, 32)
            .padding(.bottom, 48)
        }
    }

    private func createShelf() {
        Task {
            do {
                let name = shelfName.isEmpty ? nil : shelfName
                let shelf = try await ShelfService.shared.createShelf(
                    name: name,
                    rowCount: rowCount,
                    columnCount: columnCount
                )
                onCreated(shelf)
                dismiss()
            } catch {
                // Error handled by parent
            }
        }
    }
}
