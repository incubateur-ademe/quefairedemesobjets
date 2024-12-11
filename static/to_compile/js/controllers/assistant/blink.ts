import { Controller } from "@hotwired/stimulus";

export default class extends Controller<HTMLSpanElement> {
  words: Array<string> = [];
  currentWordIndex: number = 0
  currentLetterIndex: number = 0
  deleting: boolean = false
  declare readonly wordsValue: Array<string>;
  static values = {
    words: Array,
  };

  initialize() {
    this.words = [this.element.textContent!.trim(), ...this.wordsValue];
  }

  connect() {
    this.loopWords()
  }

  loopWords() {
    const currentWord = this.words[this.currentWordIndex];
    let updatedText: string;

    if (this.deleting) {
      // Remove one letter
      updatedText = currentWord.slice(0, this.currentLetterIndex - 1);
      this.currentLetterIndex--;
    } else {
      // Add one letter
      updatedText = currentWord.slice(0, this.currentLetterIndex + 1);
      this.currentLetterIndex++;
    }

    this.element.textContent = updatedText;

    // Determine next step
    if (!this.deleting && this.currentLetterIndex === currentWord.length) {
      // Pause after full word is written
      this.deleting = true;
      setTimeout(() => this.loopWords(), 2000); // Longer pause after writing a word
    } else if (this.deleting && this.currentLetterIndex === 0) {
      // Move to next word after full deletion
      this.deleting = false;
      this.currentWordIndex = (this.currentWordIndex + 1) % this.words.length;
      setTimeout(() => this.loopWords(), 500); // Shorter pause before typing next word
    } else {
      // Continue typing or deleting
      setTimeout(
        () => this.loopWords(),
        this.deleting ? 50 : 150 // Deleting speed is faster (50ms), typing speed is slower (150ms)
      );
    }
  }
}
