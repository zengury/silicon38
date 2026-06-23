import SwiftUI
import AVFoundation

/// Camera view with shelf alignment guide.
/// States: idle → capturing → preview → uploading → processing → done
enum CameraState {
    case ready
    case captured(UIImage)
    case uploading
    case processing(String)  // jobId
    case done([Book])
    case error(String)
}

struct CameraView: View {
    let shelfId: String
    let shelfName: String
    let rowCount: Int
    let columnCount: Int

    @Environment(\.dismiss) private var dismiss
    @StateObject private var model = CameraViewModel()

    var body: some View {
        ZStack {
            Color.black.ignoresSafeArea()

            switch model.state {
            case .ready:
                cameraPreview

            case .captured(let image):
                photoPreview(image: image)

            case .uploading:
                uploadingView

            case .processing(let jobId):
                processingView(jobId: jobId)

            case .done(let books):
                doneView(books: books)

            case .error(let message):
                errorView(message: message)
            }
        }
        .navigationBarTitleDisplayMode(.inline)
        .navigationBarBackButtonHidden(model.state != .done && model.state != .ready)
        .task {
            model.shelfId = shelfId
            model.rowCount = rowCount
            model.columnCount = columnCount
            await model.checkPermission()
        }
    }

    // MARK: - Camera Preview

    private var cameraPreview: some View {
        ZStack {
            CameraPreview(session: model.session)
                .ignoresSafeArea()

            // Shelf alignment guide — per UX spec
            VStack(spacing: 0) {
                Color.black.opacity(0.4)
                ForEach(0..<rowCount, id: \.self) { _ in
                    Rectangle()
                        .stroke(Color.white.opacity(0.6), lineWidth: 1)
                        .background(Color.white.opacity(0.05))
                }
                Color.black.opacity(0.4)
            }
            .ignoresSafeArea()

            // Instructional text
            VStack {
                Spacer()
                Text("Frame your shelf so all books are visible")
                    .font(.subheadline)
                    .foregroundColor(.white)
                    .padding(12)
                    .background(.ultraThinMaterial)
                    .clipShape(RoundedRectangle(cornerRadius: 10))
                    .padding(.bottom, 120)
            }
        }
        .overlay(alignment: .bottom) {
            Button(action: model.capture) {
                ZStack {
                    Circle()
                        .stroke(Color.white, lineWidth: 3)
                        .frame(width: 74, height: 74)
                    Circle()
                        .fill(Color.white)
                        .frame(width: 62, height: 62)
                }
            }
            .padding(.bottom, 48)
        }
        .overlay(alignment: .topTrailing) {
            Button(action: { dismiss() }) {
                Image(systemName: "xmark.circle.fill")
                    .font(.title)
                    .foregroundColor(.white)
                    .padding()
            }
        }
    }

    // MARK: - Photo Preview

    private func photoPreview(image: UIImage) -> some View {
        VStack {
            HStack {
                Button("Retake") { model.state = .ready }
                    .foregroundColor(.white)
                Spacer()
                Button("Use Photo →") { Task { await model.upload(image) } }
                    .fontWeight(.semibold)
                    .foregroundColor(.white)
            }
            .padding()

            Image(uiImage: image)
                .resizable()
                .aspectRatio(contentMode: .fit)
                .clipShape(RoundedRectangle(cornerRadius: 12))
                .padding()

            Text("Does this show the full shelf clearly?")
                .font(.subheadline)
                .foregroundColor(.white.opacity(0.8))

            Spacer()
        }
        .background(Color.black)
    }

    // MARK: - Uploading & Processing

    private var uploadingView: some View {
        VStack(spacing: 24) {
            Image(systemName: "books.vertical.fill")
                .font(.system(size: 48))
                .foregroundColor(.brown)

            Text("Recognizing your books...")
                .font(.title3)
                .foregroundColor(.white)

            ProgressView()
                .scaleEffect(1.5)
                .tint(.brown)

            Text("This usually takes about 10 seconds")
                .font(.caption)
                .foregroundColor(.white.opacity(0.6))
        }
    }

    private func processingView(jobId: String) -> some View {
        VStack(spacing: 24) {
            Image(systemName: "sparkles")
                .font(.system(size: 48))
                .foregroundColor(.brown)

            Text("Almost there...")
                .font(.title3)
                .foregroundColor(.white)

            ProgressView()
                .scaleEffect(1.5)
                .tint(.brown)

            Text("AI is reading your books")
                .font(.caption)
                .foregroundColor(.white.opacity(0.6))
        }
        .task {
            await model.pollUntilComplete(jobId: jobId)
        }
    }

    // MARK: - Done

    private func doneView(books: [Book]) -> some View {
        VStack(spacing: 16) {
            Spacer()

            Image(systemName: "checkmark.circle.fill")
                .font(.system(size: 64))
                .foregroundColor(.green)

            Text("\(books.count) Books Recognized")
                .font(.title2)
                .fontWeight(.bold)
                .foregroundColor(.white)

            Text("Your shelf \"\(shelfName)\" is ready")
                .foregroundColor(.white.opacity(0.8))

            if model.needsReviewCount > 0 {
                HStack {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .foregroundColor(.yellow)
                    Text("\(model.needsReviewCount) books need your review")
                        .foregroundColor(.yellow)
                }
                .font(.caption)
            }

            Spacer()

            Button(action: { dismiss() }) {
                Text("View Shelf")
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
        .background(Color.black)
    }

    // MARK: - Error

    private func errorView(message: String) -> some View {
        VStack(spacing: 16) {
            Spacer()

            Image(systemName: "exclamationmark.triangle.fill")
                .font(.system(size: 48))
                .foregroundColor(.orange)

            Text("Something went wrong")
                .font(.title3)
                .foregroundColor(.white)

            Text(message)
                .font(.body)
                .foregroundColor(.white.opacity(0.7))
                .multilineTextAlignment(.center)
                .padding(.horizontal, 32)

            Button("Try Again") {
                model.state = .ready
            }
            .font(.headline)
            .foregroundColor(.white)
            .padding(.horizontal, 32)
            .padding(.vertical, 12)
            .background(Color.brown)
            .clipShape(RoundedRectangle(cornerRadius: 10))

            Spacer()
        }
        .background(Color.black)
    }
}

// MARK: - Camera ViewModel

@MainActor
class CameraViewModel: ObservableObject {
    @Published var state: CameraState = .ready
    @Published var needsReviewCount = 0

    var shelfId = ""
    var rowCount = 0
    var columnCount = 0

    let session = AVCaptureSession()
    private let output = AVCapturePhotoOutput()

    func checkPermission() async {
        let status = AVCaptureDevice.authorizationStatus(for: .video)
        switch status {
        case .authorized:
            setupCamera()
        case .notDetermined:
            let granted = await AVCaptureDevice.requestAccess(for: .video)
            if granted { setupCamera() }
        default:
            state = .error("Camera access is required. Enable it in Settings.")
        }
    }

    private func setupCamera() {
        session.beginConfiguration()
        session.sessionPreset = .photo

        guard let device = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .back),
              let input = try? AVCaptureDeviceInput(device: device),
              session.canAddInput(input),
              session.canAddOutput(output) else {
            state = .error("Could not access camera")
            return
        }

        session.addInput(input)
        session.addOutput(output)
        session.commitConfiguration()

        DispatchQueue.global(qos: .background).async { [weak self] in
            self?.session.startRunning()
        }
    }

    func capture() {
        let settings = AVCapturePhotoSettings()
        output.capturePhoto(with: settings, delegate: PhotoDelegate { [weak self] image in
            Task { @MainActor in
                self?.state = .captured(image)
            }
        })
    }

    func upload(_ image: UIImage) async {
        state = .uploading
        guard let data = image.jpegData(compressionQuality: 0.85) else {
            state = .error("Could not process photo")
            return
        }

        do {
            let job = try await BookService.shared.startRecognition(shelfId: shelfId, imageData: data)
            state = .processing(job.jobId)
        } catch {
            state = .error(error.localizedDescription)
        }
    }

    func pollUntilComplete(jobId: String) async {
        for _ in 0..<30 {  // max 30 polls (30s timeout)
            do {
                let job = try await BookService.shared.pollRecognition(shelfId: shelfId, jobId: jobId)
                switch job.status {
                case "completed":
                    let books = job.books ?? []
                    needsReviewCount = books.filter { ($0.confidence ?? 1.0) < 0.7 }.count
                    state = .done(books)
                    return
                case "failed":
                    state = .error(job.error ?? "Recognition failed")
                    return
                default:
                    try await Task.sleep(nanoseconds: 1_000_000_000)
                }
            } catch {
                try? await Task.sleep(nanoseconds: 1_000_000_000)
            }
        }
        state = .error("Recognition timed out. Please try again.")
    }
}

// MARK: - Camera Preview (UIViewRepresentable)

struct CameraPreview: UIViewRepresentable {
    let session: AVCaptureSession

    func makeUIView(context: Context) -> UIView {
        let view = UIView()
        let preview = AVCaptureVideoPreviewLayer(session: session)
        preview.videoGravity = .resizeAspectFill
        view.layer.addSublayer(preview)
        return view
    }

    func updateUIView(_ uiView: UIView, context: Context) {
        if let layer = uiView.layer.sublayers?.first as? AVCaptureVideoPreviewLayer {
            layer.frame = uiView.bounds
        }
    }
}

// MARK: - Photo Delegate

class PhotoDelegate: NSObject, AVCapturePhotoCaptureDelegate {
    private let onCapture: (UIImage) -> Void

    init(onCapture: @escaping (UIImage) -> Void) {
        self.onCapture = onCapture
    }

    func photoOutput(_ output: AVCapturePhotoOutput, didFinishProcessingPhoto photo: AVCapturePhoto, error: Error?) {
        guard let data = photo.fileDataRepresentation(),
              let image = UIImage(data: data) else { return }
        onCapture(image)
    }
}
