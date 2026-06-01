import time

def main() -> None:
    t0 = time.time()
    from zv.app import ZeroVisionAssistant
    print(f"Import zv.app took {time.time()-t0:.2f}s")

    t1 = time.time()
    app = ZeroVisionAssistant()
    print(f"Construct app took {time.time()-t1:.2f}s")

    from api.services import llm_service
    llm_service._ensure_qa_loaded()
    
    app.mainloop()

if __name__ == "__main__":
    main()