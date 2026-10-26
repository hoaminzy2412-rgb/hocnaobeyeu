/* Microphone recording core: no network requests, only explicit user activation. */
(function (root) {
  'use strict';
  class ChildVoiceRecorder {
    constructor(options = {}) {
      this.env = options.env || root;
      this.onChange = options.onChange || (() => {});
      this.maxSeconds = options.maxSeconds || 600;
      this.maxBytes = options.maxBytes || 25 * 1024 * 1024;
      this.state = 'idle'; this.message = ''; this.file = null; this.url = '';
      this.stream = null; this.recorder = null; this.chunks = [];
      this._timer = null; this._elapsed = 0; this._activeSince = null;
      this._generation = 0; this._stopPromise = null; this._stopResolve = null;
      this._clock = options.clock || (() => this.env.performance.now());
      this._recordedBytes = 0;
    }
    get seconds() {return (this._elapsed + (this._activeSince === null ? 0 : Math.max(0, this._clock() - this._activeSince))) / 1000;}
    get busy() {return ['requesting', 'recording', 'paused', 'stopping'].includes(this.state);}
    get unsaved() {return this.busy || Boolean(this.file);}
    _emit(message) {if (message !== undefined) this.message = message; this.onChange(this);}
    _finishClock() {if (this._activeSince !== null) {this._elapsed += Math.max(0, this._clock() - this._activeSince); this._activeSince = null;}}
    _tracksOff() {if (this.stream) {this.stream.getTracks().forEach(t => {try {t.stop();} catch {}}); this.stream = null;}}
    _clearTimer() {if (this._timer !== null) {this.env.clearInterval(this._timer); this._timer = null;}}
    _clearFile() {if (this.url) {this.env.URL.revokeObjectURL(this.url); this.url = '';} this.file = null;}
    _chooseMime() {
      const M = this.env.MediaRecorder;
      return ['audio/mp4;codecs=mp4a.40.2', 'audio/mp4', 'audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus', 'audio/ogg'].find(m => typeof M.isTypeSupported === 'function' && M.isTypeSupported(m)) || '';
    }
    async start() {
      if (this.state === 'disposed') throw new Error('Bảng thu âm đã đóng. Mở lại bài học để thu.');
      if (this.busy) throw new Error('Hãy dừng bản thu hiện tại trước.');
      if (this.env.isSecureContext === false || !this.env.navigator?.mediaDevices?.getUserMedia) {
        this.state = 'error'; this._emit('Thu âm cần HTTPS hoặc localhost. Có thể thu bằng ứng dụng trên máy rồi tải tệp lên.');
        throw new Error(this.message);
      }
      if (!this.env.MediaRecorder) {
        this.state = 'error'; this._emit('Trình duyệt chưa hỗ trợ thu âm. Dùng Chrome/Edge/Safari mới hoặc tải bản thu có sẵn.');
        throw new Error(this.message);
      }
      const generation = ++this._generation;
      this.state = 'requesting'; this._emit('Bố mẹ bấm Cho phép khi trình duyệt hỏi quyền micro.');
      let stream;
      try {
        stream = await this.env.navigator.mediaDevices.getUserMedia({audio: {echoCancellation: true, noiseSuppression: true, autoGainControl: true}, video: false});
        if (this.state === 'disposed' || generation !== this._generation) {stream.getTracks().forEach(t => t.stop()); return;}
        const mime = this._chooseMime();
        const recorder = new this.env.MediaRecorder(stream, mime ? {mimeType: mime, audioBitsPerSecond: 96000} : {audioBitsPerSecond: 96000});
        this._clearFile(); this.stream = stream; this.recorder = recorder; this.chunks = [];
        this._elapsed = 0; this._recordedBytes = 0; this._activeSince = null;
        this._stopPromise = null; this._stopResolve = null;
        recorder.ondataavailable = event => {
          if (this.state === 'disposed' || generation !== this._generation) return;
          if (event.data?.size) {this.chunks.push(event.data); this._recordedBytes += event.data.size;}
          if (this._recordedBytes >= this.maxBytes - 128 * 1024 && ['recording', 'paused'].includes(this.state)) {
            this._emit('Bản thu gần giới hạn dung lượng, đang dừng để giữ bài.');
            this.stop().catch(() => {});
          }
        };
        recorder.onerror = () => {
          if (this.state === 'disposed') return;
          this._finishClock(); this._clearTimer(); this._tracksOff(); this.state = 'error';
          this._emit('Micro hoặc trình ghi âm gặp lỗi. Bố mẹ kiểm tra thiết bị rồi thu lại.');
          if (this._stopResolve) {this._stopResolve(null); this._stopResolve = null;}
        };
        recorder.onstop = () => {
          this._finishClock(); this._clearTimer(); this._tracksOff();
          if (this.state === 'disposed' || generation !== this._generation) {if (this._stopResolve) this._stopResolve(null); return;}
          if (this.state === 'error') {if (this._stopResolve) this._stopResolve(null); return;}
          const actual = recorder.mimeType || this.chunks[0]?.type || mime || 'audio/webm';
          if (!/audio\/(mp4|webm|ogg|wav)/i.test(actual)) {
            this.state = 'error'; this._emit('Định dạng thu của trình duyệt chưa được hỗ trợ. Hãy dùng Chrome/Edge/Safari mới hoặc tải tệp âm thanh có sẵn.');
            if (this._stopResolve) {this._stopResolve(null); this._stopResolve = null;} return;
          }
          const blob = new this.env.Blob(this.chunks, {type: actual});
          this.chunks = [];
          if (!blob.size || blob.size > this.maxBytes) {
            this.state = 'error'; this._emit(blob.size ? 'Bản thu vượt 25 MB. Hãy thu ngắn hơn.' : 'Chưa ghi được âm thanh. Kiểm tra micro và thu lại.');
            if (this._stopResolve) {this._stopResolve(null); this._stopResolve = null;} return;
          }
          const ext = actual.includes('mp4') ? 'm4a' : actual.includes('ogg') ? 'ogg' : actual.includes('wav') ? 'wav' : 'webm';
          this.file = new this.env.File([blob], 'bai-thu-am-' + Date.now() + '.' + ext, {type: actual});
          this.url = this.env.URL.createObjectURL(this.file); this.state = 'ready';
          this._emit('Đã thu xong. Bố mẹ cho con nghe lại, thu lại hoặc bấm Gửi bài cho cô.');
          if (this._stopResolve) {this._stopResolve(this.file); this._stopResolve = null;}
        };
        stream.getAudioTracks().forEach(track => track.addEventListener?.('ended', () => {
          if (['recording', 'paused'].includes(this.state)) this.stop().catch(() => {});
        }));
        recorder.start(1000); this._activeSince = this._clock(); this.state = 'recording';
        this._emit('Đang thu âm… Bé đọc thơ, kể chuyện hoặc hát nhé!');
        this._timer = this.env.setInterval(() => {
          if (this.state === 'disposed') return;
          if (this.seconds >= this.maxSeconds && ['recording', 'paused'].includes(this.state)) {
            this._emit('Đã tới 10 phút, đang dừng bản thu.'); this.stop().catch(() => {});
          } else this._emit();
        }, 500);
      } catch (error) {
        if (stream) stream.getTracks().forEach(t => {try {t.stop();} catch {}});
        if (this.state === 'disposed' || generation !== this._generation) return;
        this._tracksOff(); this._clearTimer(); this.state = 'error';
        const messages = {NotAllowedError: 'Chưa được cấp quyền micro. Bố mẹ cho phép micro trong trình duyệt rồi thử lại.', NotFoundError: 'Không tìm thấy micro. Kết nối micro hoặc chọn thiết bị khác.', NotReadableError: 'Micro đang bận hoặc bị hệ điều hành chặn. Đóng ứng dụng đang dùng micro rồi thử lại.', SecurityError: 'Trình duyệt đang chặn micro. Mở web bằng HTTPS hoặc localhost.'};
        this._emit(messages[error.name] || 'Không mở được micro. Bố mẹ kiểm tra quyền và thiết bị rồi thử lại.');
        throw new Error(this.message);
      }
    }
    pause() {if (this.state !== 'recording') return; this.recorder.pause(); this._finishClock(); this.state = 'paused'; this._emit('Đã tạm dừng. Bấm Tiếp tục hoặc Dừng và nghe lại.');}
    resume() {if (this.state !== 'paused') return; this.recorder.resume(); this._activeSince = this._clock(); this.state = 'recording'; this._emit('Đang thu âm tiếp…');}
    stop() {
      if (this.state === 'ready') return Promise.resolve(this.file);
      if (this.state === 'stopping') return this._stopPromise;
      if (!['recording', 'paused'].includes(this.state)) return Promise.resolve(null);
      this._finishClock(); this.state = 'stopping'; this._clearTimer();
      this._stopPromise = new Promise(resolve => {this._stopResolve = resolve;});
      this._emit('Đang hoàn tất bản thu…');
      try {this.recorder.stop(); this._tracksOff();} catch {this._tracksOff(); this.state = 'error'; this._emit('Không thể hoàn tất bản thu. Hãy thử lại.'); this._stopResolve(null); this._stopResolve = null;}
      return this._stopPromise;
    }
    discard() {
      if (this.busy) throw new Error('Dừng thu âm trước khi bỏ bản thu.');
      this._clearFile(); this._elapsed = 0; this._activeSince = null; this.state = 'idle'; this._emit('Chưa có bản thu.');
    }
    dispose() {
      if (this.state === 'disposed') return;
      ++this._generation; this._finishClock(); this._clearTimer(); this.state = 'disposed';
      if (this.recorder && this.recorder.state !== 'inactive') {try {this.recorder.stop();} catch {}}
      this._tracksOff(); this._clearFile(); this.chunks = [];
      if (this._stopResolve) {this._stopResolve(null); this._stopResolve = null;}
    }
  }
  root.ChildVoiceRecorder = ChildVoiceRecorder;
  if (typeof module !== 'undefined' && module.exports) module.exports = {ChildVoiceRecorder};
})(typeof window !== 'undefined' ? window : globalThis);
